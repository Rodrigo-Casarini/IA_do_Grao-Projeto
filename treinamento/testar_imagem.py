from ultralytics import YOLO

model = YOLO(r"C:\Users\CTDEV2025\Documents\IA_do_Grao\treinamento\runs\detect\train\weights\best.pt")
results = model(r"C:\Users\CTDEV2025\Documents\IA_do_Grao\treinamento\images\val\1_bom.jpg", save=True, conf=0.15)

print("[+] Concluído!")


#from pathlib import Path

#from ultralytics import YOLO

#root = Path(__file__).parent
#model = YOLO(root / r"C:\Users\Rodrigo\Downloads\IA_do_Grao\treinamento\runs\detect\train\weights\best.pt")
#results = model(root / "teste", save=True, conf=0.25)

#print("[+] Concluído!")
