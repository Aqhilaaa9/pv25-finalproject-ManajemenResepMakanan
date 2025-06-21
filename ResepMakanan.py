import sys
import sqlite3
import csv
from PyQt5.QtCore import Qt
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidgetItem, QFileDialog, QMessageBox, QInputDialog, QDockWidget, QTextEdit
)

# Inisialisasi database
def init_db():
    conn = sqlite3.connect("resepmakanan.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resep (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT,
            kategori TEXT,
            tanggal TEXT,
            kesulitan TEXT,
            catatan TEXT,
            bahan TEXT
        )
    """)
    conn.commit()
    conn.close()

class ResepApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ResepMakanan.ui", self)
        self.resize(1020, 800) 

        self.setWindowTitle("Manajemen Resep Masakan")

        # Hubungkan tombol ke fungsi
        self.tambah_btn.clicked.connect(self.tambah_resep)
        self.ekspor_btn.clicked.connect(self.ekspor_csv)
        self.hapus_btn.clicked.connect(self.hapus_resep)

        # Hubungkan klik ganda ke fungsi edit
        self.table.cellDoubleClicked.connect(self.edit_resep)

        # Hubungkan menu Help dan Exit
        self.actionExit.triggered.connect(self.keluar_aplikasi)
        self.actionHelp.triggered.connect(self.tampilkan_bantuan)

        self.create_dock_widget()

        self.load_data()

    def tambah_resep(self):
        nama = self.nama_input.text()
        kategori = self.kategori_input.currentText()
        tanggal = self.tanggal_input.text()
        kesulitan = self.kesulitan_input.currentText()
        bahan = self.bahan_input.toPlainText()
        catatan = self.catatan_input.toPlainText()

        if not nama or not kategori or not bahan:
            QMessageBox.warning(self, "Peringatan", "Nama, Kategori, dan Bahan wajib diisi!")
            return

        conn = sqlite3.connect("resepmakanan.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO resep (nama, kategori, tanggal, kesulitan, bahan, catatan)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nama, kategori, tanggal, kesulitan, bahan, catatan))
        conn.commit()
        conn.close()

        self.clear_inputs()
        self.load_data()

    def hapus_resep(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Peringatan", "Pilih resep yang ingin dihapus.")
            return

        id_item = self.table.item(selected_row, 0)
        nama_item = self.table.item(selected_row, 1)

        if not id_item:
            return

        resep_id = id_item.text()
        nama_resep = nama_item.text() if nama_item else "(Tanpa Nama)"

        reply = QMessageBox.question(
            self, "Konfirmasi", f"Yakin ingin menghapus resep '{nama_resep}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            conn = sqlite3.connect("resepmakanan.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM resep WHERE id = ?", (resep_id,))
            conn.commit()
            conn.close()
            self.load_data()

    def edit_resep(self, row, column):
        try:
            # Ambil ID dari baris yang diklik (kolom 0 disembunyikan tapi tetap bisa diakses)
            resep_id = int(self.table.item(row, 0).text())

            # Daftar nama kolom di database sesuai index
            kolom_nama = {
                1: "nama",
                2: "kategori",
                3: "tanggal",
                4: "kesulitan",
                5: "bahan",
                6: "catatan"
            }

            if column not in kolom_nama:
                QMessageBox.information(self, "Info", "Kolom ini tidak bisa diedit langsung.")
                return
            
            current_value = self.table.item(row, column).text()

            # Pilih jenis dialog berdasarkan kolom
            if column in [5, 6]:
                new_value, ok = QInputDialog.getMultiLineText(self, "Edit", f"Ubah {kolom_nama[column].capitalize()}:", text=current_value)
            else:
                new_value, ok = QInputDialog.getText(self, "Edit", f"Ubah {kolom_nama[column].capitalize()}:", text=current_value)

            if not ok or not new_value.strip():
                return

            # Update hanya kolom yang diedit
            conn = sqlite3.connect("resepmakanan.db")
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE resep 
                SET {kolom_nama[column]} = ? 
                WHERE id = ?
            """, (new_value.strip(), resep_id))
            conn.commit()
            conn.close()

            self.load_data()
            QMessageBox.information(self, "Sukses", f"{kolom_nama[column].capitalize()} berhasil diperbarui.")

        except Exception as e:
            QMessageBox.critical(self, "Kesalahan", f"Terjadi kesalahan:\n{str(e)}")


    def load_data(self):
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Nama", "Kategori", "Tanggal", "Kesulitan", "Bahan", "Catatan"])
        self.table.setRowCount(0)

        conn = sqlite3.connect("resepmakanan.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, nama, kategori, tanggal, kesulitan, bahan, catatan FROM resep")
        for row_index, row_data in enumerate(cursor.fetchall()):
            self.table.insertRow(row_index)
            for col_index, data in enumerate(row_data):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(data)))

        self.table.setColumnHidden(0, True)
        conn.close()

    def ekspor_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Simpan File", "", "CSV Files (*.csv)")
        if path:
            conn = sqlite3.connect("resepmakanan.db")
            cursor = conn.cursor()
            cursor.execute("SELECT nama, kategori, tanggal, kesulitan, bahan, catatan FROM resep")
            data = cursor.fetchall()
            conn.close()

            with open(path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Nama", "Kategori", "Tanggal", "Kesulitan", "Bahan", "Catatan"])
                writer.writerows(data)

            QMessageBox.information(self, "Sukses", "Data berhasil diekspor ke CSV!")

    def clear_inputs(self):
        self.nama_input.clear()
        self.kategori_input.clear()
        self.tanggal_input.clear()
        self.kesulitan_input.setCurrentIndex(0)
        self.bahan_input.clear()
        self.catatan_input.clear()

    def keluar_aplikasi(self):
        reply = QMessageBox.question(
            self, "Konfirmasi Keluar", "Apakah Anda yakin ingin keluar dari aplikasi?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QApplication.quit()

    def tampilkan_bantuan(self):
        QMessageBox.information(
            self,
            "Bantuan",
            "Ini adalah aplikasi Manajemen Resep Masakan.\n\n"
            "Panduan Aplikasi sebagai berikut: \n"
            "- Tambah: Menyimpan resep baru.\n"
            "- Hapus: Menghapus resep yang dipilih.\n"
            "- Ekspor: Menyimpan semua resep ke file CSV.\n"
            "- Klik dua kali pada tabel untuk mengedit data.\n"
            "- Menu File → Exit untuk keluar dari aplikasi."
        )
    
    def create_dock_widget(self):
        self.dock = QDockWidget("Petunjuk Aplikasi", self)
        dock_text = QTextEdit("Aplikasi ini dapat digunakan untuk memenajemen/menyimpan resep makan dari pengguna. Untuk petunjuk lebih lanjut Anda dapat menakan tombol file di sebelah kiri atas dan menekan tombol bantuan")
        dock_text.setReadOnly(True)
        self.dock.setWidget(dock_text)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock)

if __name__ == '__main__':
    init_db()
    app = QApplication(sys.argv)
    window = ResepApp()
    window.show()
    sys.exit(app.exec_())
