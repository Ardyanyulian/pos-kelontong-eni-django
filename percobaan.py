class Manusia:
    def __init__(self, nama):
        self.nama = nama
    
    def cetakInfo(self):
        return f"Nama saya adalah {self.nama}"
    
class pembeli(Manusia):
    def __init__(self, nama):
        super().__init__(nama)
    
    def cetakInfo(self):
        self.cetakInfo
        return f"Saldo saya adalah {self.saldo}"

class kasir(Manusia):
    def __init__(self, nama):
        super().__init__(nama)
        self.pesanan = []