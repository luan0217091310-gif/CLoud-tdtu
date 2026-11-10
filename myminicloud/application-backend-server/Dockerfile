FROM python:3.11-alpine
WORKDIR /app
RUN apk add --no-cache bind-tools curl iputils
COPY app.py students.json ./
RUN pip install --no-cache-dir flask requests "python-jose[cryptography]" pymysql
EXPOSE 8081
CMD ["python", "app.py"]

