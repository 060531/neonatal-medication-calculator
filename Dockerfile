# ใช้ base image ที่รองรับ Flask
FROM python:3.9

# ตั้งค่าตำแหน่งในการทำงานใน container
WORKDIR /app

# คัดลอกไฟล์ไปยัง container
COPY . /app

# ติดตั้ง dependencies
RUN pip install -r requirements.txt

# ระบุ port ที่ต้องการให้ container ฟัง
EXPOSE 8080

# รันแอป
CMD ["python", "app.py"]
