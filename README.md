# 🧠 Radial Arm Maze Automation

[**⚙️ System: RAM_Analysis.py**](Backend/RAM_Analysis.py)

---

## 📚 Tentang Radial Arm Maze (RAM)
Radial Arm Maze adalah **maze berbentuk bintang** dengan beberapa “arm” yang digunakan dalam eksperimen perilaku hewan, terutama tikus, untuk menguji:  
- **Memori spasial** dan kemampuan belajar  
- **Efektivitas suatu obat atau terapi** dalam meningkatkan fungsi kognitif atau perilaku  

Dengan sistem RAM Automation ini, proyek bertujuan untuk:  
- Mendeteksi pergerakan hewan dalam setiap arm secara otomatis  
- Menghasilkan evaluasi akurat secara otomatis
- Mempermudah penelitian farmakologis

---

## 🗂️ Dataset
Maaf, dataset berupa video mentah yang telah diklasifikasikan:  
[**📄 Dataset Training (evalOutput.csv)**](Backend/evaluationData/evalOutput.csv)

---

## 🛠️ Teknologi & Libraries
**Front End:**  
- ⚛️ React

**Backend / Python Libraries:**  
- 🐍 Python  
- 📹 OpenCV (`opencv-python`)  
- 🔢 NumPy (`numpy`)  
- 📊 Pandas (`pandas`)  
- ⚡ FastAPI (`fastapi`)  
- 🏃 Uvicorn (`uvicorn`) – untuk menjalankan FastAPI

## 📈 Evaluasi Klasifikasi Random Forest
[**📂 File: evalOutput.csv**](Backend/evaluationData/evalOutput.csv)

**Perhitungan Precision:**  
$$
Precision = \frac{TP}{TP+FP}
$$
$$
Precision = \frac{1967}{1967+356}
$$
$$
Precision = \frac{1967}{2323}
$$
$$
Precision =  0.8467
$$
<hr>

---

## 🧪 Evaluasi Fungsionalitas

**Bukti Hasil:** [📁 Google Drive Folder](https://drive.google.com/drive/folders/1ulK1tZRmqObCbfQGDBuP5aVvy97iIX_f?usp=drive_link)

**Keterangan:**  
- ✅ GT = Ground Truth  
- 🤖 ML = Machine Learning  
- 📈 Improvement = 30%

![Hasil Evaluasi](https://github.com/user-attachments/assets/dc719e29-d9dd-4bb5-a210-ec0389fd8d0c)

---
