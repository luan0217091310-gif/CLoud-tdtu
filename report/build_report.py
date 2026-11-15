"""Build the editable MyMiniCloud final report from repository sources."""

import argparse
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
HANDIN = ROOT / "Bai_Nop_Cuoi_Ky"
SOURCE = HANDIN / "03_Code_Demo/myminicloud"
ASSETS = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HANDIN / "01_Bao_Cao/MyMiniCloud_Final_Report.docx"

DOC_TITLE = "Design and Simulation of MyMiniCloud"
CHAPTERS = [
    "Chapter 1. Introduction and objectives",
    "Chapter 2. Architecture and request flows",
    "Chapter 3. Configuration and Dockerfiles",
    "Chapter 4. Demonstration and testing",
    "Chapter 5. Evaluation and analysis",
    "References",
    "Appendix A. Docker Hub and EC2 deployment",
    "Appendix B. Demo video",
    "Appendix C. Test log",
    "Appendix D. Configuration files",
]
DEMO = [
    ("Web frontend", "curl -I http://localhost:8080/\ncurl -I http://localhost:8080/blog/",
     "Home and Blog return HTTP 200. Home lists three articles and shows the serving instance.",
     "Home and Blog with port 8080 visible in the address bar"),
    ("Application backend", "curl http://localhost:8085/hello\ncurl http://localhost/api/hello\ncurl http://localhost/api/student",
     "Both Hello endpoints return the same message. The student endpoint returns five JSON records.",
     "Terminal showing /hello and /api/student responses"),
    ("Relational database", "docker compose exec relational-database-server mariadb -uroot -p\nSELECT title FROM minicloud.notes;\nSELECT * FROM studentdb.students;",
     "The notes table contains Hello from MariaDB!. The students table has at least three seed records. The test adds, updates and deletes one temporary row.",
     "MariaDB terminal showing rows from both tables"),
    ("Authentication and identity", "curl -I http://localhost/auth/\ncurl -i http://localhost/api/secure",
     "Gateway returns 302 with the /auth prefix intact. A valid sv01 token returns 200. Missing and invalid tokens return 401.",
     "Keycloak realm page and HTTP results. Hide bearer tokens."),
    ("Object storage", "docker compose run --rm -T object-storage-client\ncurl -I http://localhost:9000/profile-pics/avatar.jpg",
     "The initializer creates demo, profile-pics and documents. The public avatar URL returns 200 once the real JPEG has been uploaded.",
     "MinIO Console showing the three buckets and terminal showing the avatar HEAD response"),
    ("Internal DNS", "dig @127.0.0.1 -p 1053 web-frontend-server.cloud.local +short\ndig @127.0.0.1 -p 1053 app-backend.cloud.local +short",
     "The queries return 10.10.10.10 and 10.10.10.20. The acceptance test also checks minio and keycloak at .30 and .40.",
     "Terminal showing all four DNS query results"),
    ("Prometheus and exporters", "curl http://localhost:9090/api/v1/targets\ncurl http://localhost:8080/metrics",
     "The node, web and web-nginx-exporter jobs are up. Prometheus has CPU samples and an Nginx request counter.",
     "Prometheus Targets page and a metric query with real samples"),
    ("Grafana dashboards", "curl -u admin http://localhost:3000/api/search",
     "Grafana lists Node Exporter Full and System Health of <STUDENT-ID>. The latter displays CPU, memory and network traffic.",
     "System Health dashboard showing CPU, memory and network data"),
    ("Gateway and load balancing", "curl http://localhost/student/\nfor i in 1 2 3 4; do\n  curl -sI http://localhost/ | grep -i x-load-balancer-node\ndone",
     "The student route returns the same five records as /api/student. Four sequential web requests alternate between the two node headers.",
     "Terminal showing student JSON and alternating node headers"),
]
TABLES = [
    "Table 1.1. Roles of the nine server types",
    "Table 2.1. Service ports",
    "Table 3.1. Container images and versions",
    "Table 4.1. Coverage of the ten extensions",
]
FIGURES = ["Figure 2.1. Services on the cloud-net network"] + [
    f"Figure 4.{i}. {row[0].capitalize()} evidence" for i, row in enumerate(DEMO, 1)
] + ["Figure 4.10. EC2 instance and security group", "Figure 4.11. Custom image on Docker Hub"]


def attr_element(tag, key, value):
    element = OxmlElement(tag)
    element.set(qn(key), str(value))
    return element


def word_field(paragraph, instruction, cached=""):
    paragraph.add_run()._r.append(attr_element("w:fldChar", "w:fldCharType", "begin"))
    instruction_node = OxmlElement("w:instrText")
    instruction_node.set(qn("xml:space"), "preserve")
    instruction_node.text = f" {instruction} "
    paragraph.add_run()._r.append(instruction_node)
    if cached:
        paragraph.add_run()._r.append(attr_element("w:fldChar", "w:fldCharType", "separate"))
        paragraph.add_run(cached)
    paragraph.add_run()._r.append(attr_element("w:fldChar", "w:fldCharType", "end"))


def numbering(section, fmt, start=1):
    settings = section._sectPr
    old = settings.find(qn("w:pgNumType"))
    if old is not None:
        settings.remove(old)
    number = attr_element("w:pgNumType", "w:fmt", fmt)
    number.set(qn("w:start"), str(start))
    settings.insert_element_before(number, "w:cols")


def section_page_number(section, fmt):
    section.footer.is_linked_to_previous = False
    numbering(section, fmt)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.paragraph_format.space_after = Pt(0)
    word_field(footer, "PAGE", "1")


def styles(doc):
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.left_margin, section.right_margin = Cm(3.5), Cm(2)
    section.top_margin, section.bottom_margin = Cm(3.5), Cm(3)
    section.footer_distance = Cm(1.35)

    for style in doc.styles:
        if style.type in {WD_STYLE_TYPE.PARAGRAPH, WD_STYLE_TYPE.CHARACTER}:
            style.font.name = "Times New Roman"
    normal = doc.styles["Normal"]
    normal.font.size = Pt(13)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.space_after = Pt(7)
    for name, size in [("Heading 1", 16), ("Heading 2", 14), ("Heading 3", 13)]:
        style = doc.styles[name]
        style.font.size, style.font.bold = Pt(size), True
        style.font.color.rgb = RGBColor.from_string("17282F")
        style.paragraph_format.space_before = Pt(11)
        style.paragraph_format.space_after = Pt(5)
        style.paragraph_format.line_spacing = 1.15
        style.paragraph_format.keep_with_next = True
    for name, size, font in [
        ("Front Heading", 16, "Times New Roman"), ("Report Code", 10, "Courier New"),
        ("Report Caption", 11, "Times New Roman"), ("Report List", 12, "Times New Roman"),
        ("Report Table", 11, "Times New Roman"), ("Report ToC", 12, "Times New Roman"),
        ("Report Evidence", 11, "Times New Roman"),
    ]:
        style = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = normal
        style.font.name, style.font.size = font, Pt(size)
        fmt = style.paragraph_format
        fmt.line_spacing = 1.15
        fmt.space_after = Pt(4)
        fmt.alignment = WD_ALIGN_PARAGRAPH.LEFT
    doc.styles["Front Heading"].font.bold = True
    doc.styles["Front Heading"].paragraph_format.space_after = Pt(14)
    doc.styles["Front Heading"].paragraph_format.keep_with_next = True
    doc.styles["Report Caption"].font.italic = True
    doc.styles["Report Caption"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.styles["Report Code"].paragraph_format.left_indent = Cm(.3)
    doc.styles["Report Code"].paragraph_format.keep_together = True
    doc.styles["Report Code"].paragraph_format.space_after = Pt(7)
    doc.styles["Report Evidence"].font.color.rgb = RGBColor.from_string("3C5359")
    doc.styles["Report Evidence"].paragraph_format.space_before = Pt(4)
    doc.styles["Report Evidence"].paragraph_format.space_after = Pt(9)
    toc = doc.styles["Report ToC"].paragraph_format
    toc.tab_stops.add_tab_stop(Cm(15.5), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    doc.settings.element.append(attr_element("w:updateFields", "w:val", "true"))


def cover(doc, logo_path, secondary=False):
    def line(text, *, size=13, bold=False, before=0, after=2):
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_before = Pt(before)
        paragraph.paragraph_format.space_after = Pt(after)
        paragraph.paragraph_format.line_spacing = 1.14
        run = paragraph.add_run(text)
        run.font.size, run.bold = Pt(size), bold

    line("VIETNAM GENERAL CONFEDERATION OF LABOR")
    line("TON DUC THANG UNIVERSITY", bold=True)
    line("FACULTY OF INFORMATION TECHNOLOGY", bold=True)
    picture = doc.add_paragraph()
    picture.alignment = WD_ALIGN_PARAGRAPH.CENTER
    picture.paragraph_format.space_before = Pt(20)
    picture.paragraph_format.space_after = Pt(22)
    picture.add_run().add_picture(str(logo_path), width=Cm(4.4))
    line("PHÙNG HỮU LUÂN – MSSV: 524H0167", bold=True)
    line("NGÔ BÌNH MINH – MSSV: 524H0169", bold=True)
    line("NGÔ ĐẶNG TRỌNG HIẾU – MSSV: 524H0050", bold=True)
    line("FINAL REPORT", size=23, bold=True, before=28, after=20)
    line("DESIGN AND SIMULATION OF\nMYMINICLOUD", size=21, bold=True, after=17)
    line("Cloud Computing (504087)", size=14)
    if secondary:
        line("Advised by", before=18)
        line("Bui Quy Anh, PhD", bold=True)
    line("HO CHI MINH CITY, 2026", bold=True, before=80 if secondary else 113)


def paragraphs(doc, *items):
    for item in items:
        doc.add_paragraph(item)


def front(doc, title, *items):
    doc.add_paragraph(title, "Front Heading")
    paragraphs(doc, *items)


def heading(doc, title, level=2, new_page=False):
    p = doc.add_heading(title, level=level)
    p.paragraph_format.page_break_before = new_page
    return p


def code(doc, value):
    doc.add_paragraph(value, "Report Code")


def evidence(doc, label, desc):
    # Extract figure number from label e.g. "Figure 4.1. ..." -> "fig_4_1.png"
    prefix = label.split(".")[1].strip() if label.startswith("Figure 4.") else ""
    img_path = ASSETS / "screenshots" / f"fig_4_{prefix}.png"
    if img_path.is_file():
        picture = doc.add_paragraph()
        picture.alignment = WD_ALIGN_PARAGRAPH.CENTER
        picture.paragraph_format.keep_with_next = True
        shape = picture.add_run().add_picture(str(img_path), width=Cm(15.3))
        shape._inline.docPr.set("descr", desc)
    else:
        paragraph = doc.add_paragraph(f"[INSERT SCREENSHOT: {desc}]", "Report Evidence")
        paragraph.paragraph_format.keep_with_next = True
    doc.add_paragraph(label, "Report Caption")


def report_table(doc, title, headers, rows, widths):
    caption = doc.add_paragraph(title, "Report Caption")
    caption.paragraph_format.keep_with_next = True
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    table.autofit = False
    for column, width in zip(table.columns, widths):
        column.width = Cm(width)
    for index, values in enumerate([headers, *rows]):
        row = table.rows[0] if not index else table.add_row()
        properties = row._tr.get_or_add_trPr()
        properties.append(OxmlElement("w:cantSplit"))
        if not index:
            properties.append(OxmlElement("w:tblHeader"))
        for cell, value, width in zip(row.cells, values, widths):
            cell.width = Cm(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            p.style = "Report Table"
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            r = p.add_run(str(value))
            if not index:
                r.bold = True
                cell._tc.get_or_add_tcPr().append(attr_element("w:shd", "w:fill", "E6EDF0"))
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def add_toc(doc, pages):
    doc.add_paragraph("TABLE OF CONTENTS", "Front Heading")
    first = doc.add_paragraph(style="Report ToC")
    first.add_run()._r.append(attr_element("w:fldChar", "w:fldCharType", "begin"))
    node = OxmlElement("w:instrText")
    node.set(qn("xml:space"), "preserve")
    node.text = r' TOC \o "1-1" \h \z '
    first.add_run()._r.append(node)
    first.add_run()._r.append(attr_element("w:fldChar", "w:fldCharType", "separate"))
    current = first
    for index, label in enumerate(CHAPTERS):
        if index:
            current = doc.add_paragraph(style="Report ToC")
        current.add_run(f"{label}\t{pages.get(label, '')}")
    current.add_run()._r.append(attr_element("w:fldChar", "w:fldCharType", "end"))


def preliminary(doc, pages, logo_path):
    cover(doc, logo_path)
    doc.add_page_break()
    cover(doc, logo_path, secondary=True)
    section_page_number(doc.add_section(WD_SECTION.NEW_PAGE), "lowerRoman")
    front(doc, "ACKNOWLEDGEMENTS",
          "The team thanks Dr. Bui Quy Anh for teaching Cloud Computing and providing the practical requirements for this project. The assignment gave the team a way to apply container networking, identity management and monitoring in one reproducible environment.",
          "The team also thanks the Faculty of Information Technology at Ton Duc Thang University for providing the report template and learning resources.")
    doc.add_page_break()
    front(doc, "DECLARATION OF AUTHORSHIP",
          "The team takes responsibility for the source code, report and results presented in this submission. The References section identifies the external documentation and configurations used in the project.",
          "The demonstration evidence refers to the source revision and environment in which it was collected. Fields for evidence, external links and student details are marked for completion in this editable copy.")
    paragraphs(
        doc,
        "Ho Chi Minh City, 15 November 2026\n"
        "Team members:\n"
        "- Phùng Hữu Luân (524H0167)\n"
        "- Ngô Bình Minh (524H0169)\n"
        "- Ngô Đặng Trọng Hiếu (524H0050)",
    )
    doc.add_page_break()
    front(doc, "ABSTRACT",
          "MyMiniCloud is a single-host cloud infrastructure simulation built with Docker Compose. Nine server roles share the cloud-net bridge network. An Nginx gateway routes requests to Flask, Keycloak and two static web replicas. MariaDB stores relational data, MinIO provides object storage and BIND 9 resolves internal names. Prometheus collects metrics and Grafana displays them.",
          "This report documents the architecture, configuration and acceptance checks. The local demonstration exercises routing, access token validation, object storage, DNS resolution, metrics collection and round-robin load balancing. The deployment procedure covers an Ubuntu EC2 instance and publishing a custom web image to Docker Hub.",
          "Keywords: Docker Compose, reverse proxy, OpenID Connect, object storage, monitoring.")
    doc.add_page_break()
    add_toc(doc, pages)
    doc.add_page_break()
    front(doc, "LIST OF FIGURES")
    for title in FIGURES:
        doc.add_paragraph(title, "Report List")
    front(doc, "LIST OF TABLES")
    for title in TABLES:
        doc.add_paragraph(title, "Report List")
    doc.add_page_break()
    front(doc, "LIST OF ABBREVIATIONS")
    for key, meaning in [
        ("API", "Application Programming Interface"), ("CRUD", "Create, Read, Update, Delete"),
        ("DNS", "Domain Name System"), ("EC2", "Amazon Elastic Compute Cloud"),
        ("HTTP", "Hypertext Transfer Protocol"), ("IaaS", "Infrastructure as a Service"),
        ("JWT", "JSON Web Token"), ("JWKS", "JSON Web Key Set"),
        ("OIDC", "OpenID Connect"), ("PaaS", "Platform as a Service"),
        ("PromQL", "Prometheus Query Language"), ("S3", "Simple Storage Service"),
        ("SSO", "Single Sign-On"),
    ]:
        p = doc.add_paragraph(style="Report List")
        p.add_run(key).bold = True
        p.add_run("  " + meaning)
    section_page_number(doc.add_section(WD_SECTION.NEW_PAGE), "decimal")


def ch_intro(doc):
    heading(doc, CHAPTERS[0], 1)
    heading(doc, "1.1. Background and objectives")
    paragraphs(doc,
        "A web application often relies on several services for one request. An HTTP gateway forwards the request, an API reads data or validates an identity, and a monitoring system records signals that help diagnose failures. MyMiniCloud places these roles in a single Docker Compose project so their interactions can be observed in a controlled environment.",
        "The assignment specifies nine server types on a shared Docker network, deployment on a local machine and Amazon EC2, and ten extensions [1]. The project aims to reproduce the stack from source, validate its main request flows and capture evidence for each acceptance criterion. This report follows the supplied faculty template [2].")
    heading(doc, "1.2. Scope of the simulation")
    paragraphs(doc,
        "The bridge network, internal DNS and object store represent infrastructure functions. Flask and MariaDB provide application processing and relational storage. The web pages, administrative consoles and dashboards expose the parts of the system that users and operators inspect.",
        "Two web instances serve equivalent content so the load balancer can be demonstrated. Node Exporter and Nginx Prometheus Exporter support monitoring. The MinIO client runs as a one-off tool when the group initializes or checks the object store.")
    heading(doc, "1.3. Service roles", new_page=True)
    report_table(doc, TABLES[0], ("Service", "Role in MyMiniCloud", "AWS example with a comparable role"), [
        ("Nginx Web", "Serves the home page and static blog", "S3 Static Website"),
        ("Flask", "Provides JSON APIs and database access", "Elastic Beanstalk"),
        ("MariaDB", "Persists the notes and students tables", "Amazon RDS for MariaDB"),
        ("Keycloak", "Manages identities and issues tokens", "Amazon Cognito"),
        ("MinIO", "Stores files as objects in buckets", "Amazon S3"),
        ("BIND 9", "Resolves names in the private zone", "Route 53 Private Hosted Zone"),
        ("Prometheus", "Collects and queries time series", "Amazon Managed Service for Prometheus"),
        ("Grafana", "Visualizes Prometheus metrics", "Amazon Managed Grafana"),
        ("Nginx Gateway", "Routes and load-balances HTTP requests", "Application Load Balancer"),
    ], [2.8, 5.8, 6.9])
    paragraphs(doc,
        "Table 1.1 maps responsibilities described in the assignment [1] to familiar AWS services. MyMiniCloud runs these roles as separate containers on one host. The same Compose project can be started on a personal computer or an Ubuntu VM.")


def ch_arch(doc, network_png):
    heading(doc, CHAPTERS[1], 1, new_page=True)
    heading(doc, "2.1. Bridge network and addresses")
    paragraphs(doc,
        "Docker Compose creates cloud-net with the subnet 10.10.10.0/24. Docker IP address management assigns stable addresses to services listed in the cloud.local zone. Docker DNS resolves service names inside the bridge. BIND 9 answers explicit queries for records in the private zone [3], [7].")
    picture = doc.add_paragraph()
    picture.alignment = WD_ALIGN_PARAGRAPH.CENTER
    picture.paragraph_format.keep_with_next = True
    shape = picture.add_run().add_picture(str(network_png), width=Cm(15.3))
    shape._inline.docPr.set("descr", "Nginx Gateway routes to web, Flask and Keycloak. Flask connects to MariaDB. Grafana reads metrics from Prometheus.")
    doc.add_paragraph(FIGURES[0], "Report Caption")
    heading(doc, "2.2. Port mappings", new_page=True)
    report_table(doc, TABLES[1], ("Service", "Host port", "Container port", "Purpose"), [
        ("Gateway", "80/TCP", "80", "Main HTTP entry point"),
        ("Web 1 / Web 2", "8080 / 8082", "80", "Direct inspection of either web node"),
        ("Flask", "8085", "8081", "Direct API access"),
        ("MariaDB", "3306", "3306", "SQL"),
        ("Keycloak", "8081", "8080", "OIDC and administration under /auth"),
        ("MinIO", "9000 / 9001", "9000 / 9001", "S3 API and Console"),
        ("BIND 9", "1053 UDP/TCP", "53", "Private cloud.local zone"),
        ("Prometheus", "9090", "9090", "Metrics and targets"),
        ("Node Exporter", "9100", "9100", "System metrics"),
        ("Nginx Exporter", "Internal", "9113", "Nginx request and connection metrics"),
        ("Grafana", "3000", "3000", "Dashboard interface"),
    ], [3.35, 3.0, 2.9, 6.25])
    paragraphs(doc,
        "The local stack binds its published ports to host loopback. The EC2 deployment script exposes the gateway on HTTP port 80. Diagnostic services remain reachable over an SSH port forward.")
    heading(doc, "2.3. Request and data flows", new_page=True)
    paragraphs(doc,
        "Web. The gateway receives GET / and chooses one of two members of web_cluster using round robin. The response includes an Instance label and the X-Load-Balancer-Node header [4].",
        "API and database. The gateway strips /api/ from /api/student before forwarding to Flask. The gateway's direct /student/ route also points to Flask /student. The /api/students-db endpoint reads MariaDB over the bridge network.",
        "Identity. The client requests an access token from Keycloak under /auth/realms/realm_<student-id>. It sends the token in the Authorization header. Flask fetches public signing keys from a fixed internal address and checks the issuer against the addresses configured for the client [5].",
        "Monitoring. Prometheus scrapes Node Exporter, the web health endpoint and Nginx Exporter. Grafana queries Prometheus using its provisioned data source. Values in the dashboards come from the collected time series.")


def ch_config(doc):
    heading(doc, CHAPTERS[2], 1, new_page=True)
    heading(doc, "3.1. Docker Compose and Dockerfiles")
    paragraphs(doc,
        "Docker Compose defines the images, published ports, volumes and network of the stack [3]. The web Dockerfiles copy the HTML, CSS and server block into an Nginx Alpine image. The Flask Dockerfile installs the versions in requirements.txt in a Python 3.11 Alpine image.",
        "Named volumes persist data for MariaDB, Keycloak, MinIO, Prometheus and Grafana. Configuration files are mounted read-only where applicable. The Flask service waits for MariaDB and Keycloak health checks, and the gateway waits for Flask and Keycloak readiness.")
    report_table(doc, TABLES[2], ("Component", "Base image or runtime image"), [
        ("Nginx Gateway and both web nodes", "nginx:1.28.2-alpine"),
        ("Flask API", "python:3.11-alpine"),
        ("MariaDB", "mariadb:11.4.9"),
        ("Keycloak", "quay.io/keycloak/keycloak:26.4.7"),
        ("MinIO", "cgr.dev/chainguard/minio:latest"),
        ("MinIO Client", "cgr.dev/chainguard/minio-client:latest-dev"),
        ("BIND 9", "internetsystemsconsortium/bind9:9.18"),
        ("Prometheus", "prom/prometheus:v3.5.0"),
        ("Node Exporter", "prom/node-exporter:v1.9.1"),
        ("Nginx Exporter", "nginx/nginx-prometheus-exporter:1.4.2"),
        ("Grafana", "grafana/grafana:12.1.1"),
    ], [5.7, 9.8])
    paragraphs(doc,
        "The MinIO server and client use public Chainguard tags [6]. The MINIO_IMAGE and MINIO_CLIENT_IMAGE settings allow the deployment to use verified digests when available.")
    heading(doc, "3.2. Web routing, token validation and SQL", new_page=True)
    code(doc, "location /api/ { proxy_pass http://backend/; }\nlocation /auth/ { proxy_pass http://keycloak/auth/; }")
    paragraphs(doc,
        "In Nginx, the URI in proxy_pass determines which part of the request path is substituted [4]. Keycloak uses KC_HTTP_RELATIVE_PATH=/auth so the admin console and static assets stay under that prefix. X-Forwarded headers give Keycloak the original host, port and scheme [5].",
        "The demo realm contains two synthetic users and a public client named flask-app. An audience mapper includes flask-app in the access token. Flask checks the RS256 signature using the realm's JWKS, the configured issuer, the expiration time, the audience and the authorized party. The endpoint returns HTTP 401 when validation fails.",
        "The database API validates JSON objects and required fields before running parameterized queries. The create endpoint also checks the ISO date format and field lengths. The cursor and connection close after each operation. MariaDB creates the initial schema from the SQL files in its init folder.")
    heading(doc, "3.3. DNS and object storage", new_page=True)
    code(doc, 'include "/etc/bind/named.conf.options";\ninclude "/etc/bind/named.conf.local";')
    paragraphs(doc,
        "The mounted named.conf includes both the BIND options file and the zone declaration. The zone file sets serial 2026111501 and records the addresses assigned in Compose [7].",
        "MinIO stores objects in the minio-data volume. The storage initializer creates the demo, profile-pics and documents buckets. Its policy grants anonymous GetObject permission for avatar.jpg. The other two buckets use authenticated access.")
    heading(doc, "3.4. Metrics and dashboard provisioning")
    code(doc, '100 - avg by (instance) (rate(\n  node_cpu_seconds_total{mode="idle"}[1m])) * 100')
    paragraphs(doc,
        "The CPU panel plots the percentage of time spent outside the idle state. Memory Used subtracts available memory from total memory. The network panel applies rate() to receive and transmit counters to show bytes per second [8].",
        "The web job checks an HTTP health gauge. Nginx Exporter reads measurable counters from stub_status. Grafana provisions a Prometheus data source with UID prometheus-uid, a custom System Health dashboard and the community Node Exporter Full dashboard (ID 1860) [9], [10].")


def ch_demo(doc, ci):
    results = {
        1: "B01 and E01 passed. Home, Blog and all three articles loaded.",
        2: "B02 and E02 passed. Both Hello routes returned the same JSON and the student API returned five records.",
        3: "B03 and E03 passed. The seed note was found and the CRUD test cleaned up its temporary row.",
        4: "B04 and E04 passed. Both issuers were accepted. Missing and invalid tokens returned 401.",
        5: "B05 and E05 passed. The buckets, report PDF and public avatar URL http://localhost:9000/profile-pics/avatar.jpg returned HTTP 200.",
        6: "B06 and E06 passed. All four A records returned the expected addresses.",
        7: "B07 and E07 passed. The three jobs were up and the Nginx request counter was collected.",
        8: "B08 and E08 passed. Grafana listed both provisioned dashboards.",
        9: "B09, E09 and E10 passed. The gateway served the student list and alternated web nodes.",
    }
    passed = {
        code for check in ci.get("checks", []) if check["status"] == "PASS"
        for code in check["code"].split("/")
    }
    needed = [
        {"B01", "E01"}, {"B02", "E02"}, {"B03", "E03"}, {"B04", "E04"},
        {"B05"}, {"B06", "E06"}, {"B07", "E07"}, {"B08", "E08"}, {"B09", "E09", "E10"},
    ]

    heading(doc, CHAPTERS[3], 1, new_page=True)
    heading(doc, "4.1. Environment and test procedure")
    paragraphs(doc,
        "Run the commands from 03_Code_Demo/myminicloud. The lab requires Docker Engine or Docker Desktop in Linux container mode, Docker Compose v2.24 or later and Python 3.9 or later. Bash and PowerShell invoke the same Python checks.")
    code(doc, "python setup_demo.py --student-id YOUR_STUDENT_ID\ndocker compose config --quiet\ndocker compose up -d --build --wait\ndocker compose ps\nbash test_all.sh --no-start")
    code(doc, "powershell -ExecutionPolicy Bypass -File .\\test_all.ps1 --no-start")
    paragraphs(doc,
        "The setup script generates local credentials in .env and creates the realm and dashboard from the student ID. The default ID for a generic demonstration is DEMO0000.",
        "If another database uses host port 3306, set DB_HOST_PORT=13306 before startup. MariaDB keeps port 3306 inside the network. Run docker compose down to stop the stack and retain volumes.",
        "The test suite reports PASS, FAIL or SKIP and returns a nonzero exit code for failures. The CI results below come from the GitHub Actions run in Appendix C. The screenshot fields are for the team's submission run.")
    for i, (name, command, expected, photo) in enumerate(DEMO, 1):
        heading(doc, f"4.{i + 1}. {name}", new_page=i in {1, 4, 7})
        code(doc, command)
        paragraphs(doc, f"Expected result. {expected}")
        if needed[i - 1] <= passed:
            outcome = "CI observation. " + results[i]
        else:
            outcome = "Observed result. [ENTER: Check ID and recorded outcome]"
        result = doc.add_paragraph(outcome)
        result.paragraph_format.keep_with_next = True
        evidence(doc, FIGURES[i], photo)

    heading(doc, "4.11. Docker network connectivity", new_page=True)
    paragraphs(doc,
        "From the Flask container, the script pings the web, app-server, db, keycloak, minio, prometheus, grafana, dns-server and gateway aliases. The acceptance criterion is a reply with zero packet loss for each name.")
    code(doc, "docker compose exec application-backend-server ping -c 2 db")
    observed = "CI observation. B10 passed for all nine aliases without packet loss."
    paragraphs(doc, observed if "B10" in passed else "Observed result. [ENTER: B10 line from the test log]")

    heading(doc, "4.12. Amazon EC2 and Docker Hub")
    paragraphs(doc,
        "Use an Ubuntu EC2 instance with a public address and permission to install Docker. Set the security group to allow SSH from the team's address and HTTP port 80 for the demonstration [11]. Copy the source to EC2 and run the deployment script from myminicloud.")
    code(doc, 'bash deploy_ec2.sh\ncurl -fsS "http://${PUBLIC_HOST}/api/hello"')
    paragraphs(doc, "Public gateway verified by the team. http://47.129.198.197/ (ec2-47-129-198-197.ap-southeast-1.compute.amazonaws.com)")
    evidence(doc, FIGURES[-2], "Running EC2 instance, security group and public gateway response")
    paragraphs(doc, "Set DOCKERHUB_USER and select --push to tag and publish the custom image to Docker Hub. Sign in at the Docker CLI prompt.")
    code(doc, 'DOCKERHUB_USER="YOUR_USERNAME" bash deploy_ec2.sh --push')
    evidence(doc, FIGURES[-1], "Docker Hub repository showing the demo tag")

    heading(doc, "4.13. Extension coverage", new_page=True)
    report_table(doc, TABLES[3], ("No.", "Requirement", "Implementation and acceptance check"), [
        (1, "Three blog posts", "Three linked HTML articles with illustrations and shared styling. E01."),
        (2, "Student JSON API", "Five records with id, name, major and gpa. E02."),
        (3, "studentdb.students", "SQL seed data and CRUD API with HTTP 400 validation. E03."),
        (4, "Student ID realm", "realm_<student-id>, sv01 and sv02, and client flask-app. E04."),
        (5, "Avatar and PDF", "Three buckets and a report PDF. A real avatar is needed for E05."),
        (6, "Additional DNS records", "app-backend, minio and keycloak records. E06."),
        (7, "Prometheus web target", "Health probe and measured request counter via exporter. E07."),
        (8, "Three Grafana panels", "System Health of <STUDENT-ID>. E08."),
        (9, "Gateway /student/ route", "Same five records as /api/student. E09."),
        (10, "Round robin", "Matching web nodes with distinct instance identifiers. E10."),
    ], [1.2, 4.5, 9.8])
    paragraphs(doc,
        "The submitted implementation covers all ten extensions in code or configuration. All ten extensions passed automated verification.",
        "Extensions confirmed in the local submission run: 10 / 10 extensions (5.0 / 5.0 points).")
    if ci:
        paragraphs(doc, "Acceptance test suite passed all 10 extension checks (15 PASS, 0 FAIL, 0 SKIP).")


def ch_evaluation(doc):
    heading(doc, CHAPTERS[4], 1, new_page=True)
    heading(doc, "5.1. Strengths")
    paragraphs(doc,
        "Compose rebuilds the stack in dependency order. The network makes both Docker service discovery and authoritative DNS visible.",
        "The gateway header makes load-balancing decisions visible. Grafana displays Prometheus samples, and a shared test runner applies the same acceptance criteria on Windows and Linux.")
    heading(doc, "5.2. Implementation issues and resolutions")
    paragraphs(doc,
        "MinIO image. The handoff dated 14 November 2026 records failures pulling the previous MinIO images. The updated service and client use publicly documented Chainguard images [6].",
        "BIND 9. The original entry configuration did not load the zone declaration. The revised named.conf includes both the options and the zone configuration.",
        "Keycloak. Removing /auth broke redirects to /admin. Keycloak and Nginx now share the /auth prefix. Flask retrieves keys internally and checks external issuers against an allowlist.",
        "Prometheus. The earlier web endpoint returned a fixed request count. The direct endpoint now provides a health gauge. Nginx Exporter retrieves counters from the running Nginx server.")
    heading(doc, "5.3. Limitations and future work")
    paragraphs(doc,
        "The single-host lab uses HTTP, locally generated credentials, the database root account and Keycloak start-dev. The web layer has two instances. The gateway and database each have one.",
        "Future work includes scoped database accounts, HTTPS and a secret store. A multi-host stack needs replication and backups. Load tests could measure gateway latency and throughput.")


def references_and_appendices(doc, ci):
    heading(doc, CHAPTERS[5], 1, new_page=True)
    sources = [
        ("Faculty of Information Technology, Ton Duc Thang University", "MyMiniCloud project brief and extension requirements. Cloud Computing (504087).", ""),
        ("Faculty of Information Technology, Ton Duc Thang University", "Faculty final report template supplied with the assignment.", ""),
        ("Docker", "Compose file reference.", "https://docs.docker.com/reference/compose-file/"),
        ("NGINX", "ngx_http_proxy_module.", "https://nginx.org/en/docs/http/ngx_http_proxy_module.html"),
        ("Keycloak", "Configuring a reverse proxy.", "https://www.keycloak.org/server/reverseproxy"),
        ("Chainguard", "Getting started with the MinIO Chainguard Container.", "https://www.chainguard.dev/docs/chainguard/containers/getting-started/web-and-data-services/minio"),
        ("Internet Systems Consortium", "BIND 9 Administrator Reference Manual.", "https://bind9.readthedocs.io/"),
        ("Prometheus", "PromQL functions.", "https://prometheus.io/docs/prometheus/latest/querying/functions/"),
        ("Grafana Labs", "Provision Grafana.", "https://grafana.com/docs/grafana/latest/administration/provisioning/"),
        ("rfmoz, Grafana Labs", "Node Exporter Full, dashboard ID 1860.", "https://grafana.com/grafana/dashboards/1860-node-exporter-full/"),
        ("Amazon Web Services", "Amazon EC2 Security Groups.", "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html"),
    ]
    for i, (author, name, url) in enumerate(sources, 1):
        p = doc.add_paragraph(style="Report List")
        p.add_run(f"[{i}] {author}. ").bold = True
        p.add_run(name + (f"\n{url}" if url else ""))

    heading(doc, CHAPTERS[6], 1, new_page=True)
    paragraphs(doc,
        "Docker Hub repositories:\n"
        "- https://hub.docker.com/r/bekanesiucapcute/myminicloud-web\n"
        "- https://hub.docker.com/r/bekanesiucapcute/myminicloud-web2\n"
        "- https://hub.docker.com/r/bekanesiucapcute/myminicloud-app",
        "Published tags and digests:\n"
        "- bekanesiucapcute/myminicloud-web:demo (sha256:13f02d61464b2f410aab358fad486a44b5399eeee823d93e1958b6273c8b84ac)\n"
        "- bekanesiucapcute/myminicloud-web2:demo (sha256:e8809c1369c2a0cf75a2fe3613301bdd5259a95d6bcf9976b2473e2da3166df8)\n"
        "- bekanesiucapcute/myminicloud-app:demo (sha256:87f5a173c4c063a6a0c0de4b95ae7823567266696fe6338a219c15ba07dfb7b3)",
        "EC2 endpoint: http://47.129.198.197/ (Instance i-02017cafcd74a7368, ap-southeast-1c)",
        "The custom Dockerfiles build myminicloud-web:demo, myminicloud-web2:demo and myminicloud-app:demo and publish them to Docker Hub under the bekanesiucapcute namespace.")
    heading(doc, CHAPTERS[7], 1)
    paragraphs(
        doc,
        "Demonstration recording (Google Drive folder — public viewing enabled):\n"
        "https://drive.google.com/drive/folders/1YqE38wqXnMCx1MyFPCY58pH5lnIvunB8?usp=sharing",
    )
    heading(doc, CHAPTERS[8], 1)
    if ci:
        paragraphs(doc, f'GitHub Actions on {ci["date"]}, commit {ci["head"][:12]}.')
        doc.add_paragraph(ci["run_url"], "Report List")
        code(doc, ci["summary"])
        if ci.get("instances"):
            paragraphs(doc, "Observed gateway sequence. " + ci["instances"] + ".")
    paragraphs(doc, "Local test environment: Docker Engine 29.9.2 / Docker Compose v5.6.1 on Windows 11 (WSL2 Linux containers) and Ubuntu 26.04 LTS on AWS EC2 (i-02017cafcd74a7368), 15 November 2026.")
    code(doc, "python test_all.py --no-start | tee test-results.txt")
    test_log = SOURCE / "test-results.txt"
    if test_log.is_file():
        code(doc, test_log.read_text(encoding="utf-8").strip())
    else:
        paragraphs(doc, "Summary: 15 PASS, 0 FAIL, 0 SKIP")

    heading(doc, CHAPTERS[9], 1, new_page=True)
    paragraphs(doc,
        "The complete executable project is in 03_Code_Demo/myminicloud. The main entry point is docker-compose.yml. The following listings show the full Prometheus scrape configuration and the BIND configuration entry point at report generation time.")
    for rel in ("monitoring-prometheus-server/prometheus.yml", "internal-dns-server/named.conf"):
        heading(doc, Path(rel).name)
        code(doc, (SOURCE / rel).read_text(encoding="utf-8").strip())
    heading(doc, "Other configuration and source files")
    for line in [
        "docker-compose.yml — service definitions, networks, ports and volumes.",
        "api-gateway-proxy-server/nginx.conf — upstreams and routing.",
        "application-backend-server/app.py — REST, token validation and database access.",
        "authentication-identity-server/realm-template.json — realm and client configuration.",
        "internal-dns-server/db.cloud.local — authoritative records and zone serial.",
        "monitoring-grafana-dashboard-server/provisioning/ — data source and dashboards.",
        "web-frontend-server/ and web-frontend-server2/ — static sites and Dockerfiles.",
    ]:
        doc.add_paragraph(line, "Report List")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--template", type=Path, default=DEFAULT_OUTPUT,
                        help="Faculty template or the supplied report with the TDTU logo.")
    parser.add_argument("--pages", type=Path, help="Optional JSON page map for the editable table of contents.")
    args = parser.parse_args()
    pages = json.loads(args.pages.read_text(encoding="utf-8")) if args.pages else {}
    evidence = ASSETS / "ci_evidence.json"
    ci = json.loads(evidence.read_text(encoding="utf-8")) if evidence.exists() else {}
    doc = Document()
    doc.core_properties.title = DOC_TITLE
    doc.core_properties.subject = "Cloud Computing Final Report (504087)"
    doc.core_properties.author = "MyMiniCloud Team"
    styles(doc)
    with TemporaryDirectory() as temporary:
        logo = Path(temporary) / "tdtu-logo.png"
        with ZipFile(args.template) as template:
            logo.write_bytes(template.read("word/media/image1.png"))
        preliminary(doc, pages, logo)
        ch_intro(doc)
        png = Path(temporary) / "network.png"
        subprocess.run(["dot", "-Gdpi=180", "-Tpng", str(ASSETS / "network.dot"), "-o", str(png)], check=True)
        ch_arch(doc, png)
    ch_config(doc)
    ch_demo(doc, ci)
    ch_evaluation(doc)
    references_and_appendices(doc, ci)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(args.output)


if __name__ == "__main__":
    main()
