from ultralytics import YOLO
import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()
    #model = YOLO("yolo11m.pt")
    model = model = YOLO(r'runs/detect/train-7/weights/best.pt')
    
    results = model.train(
        data="data.yaml",
        epochs=100,
        imgsz=640, 
        batch=10,
        workers=0,
        #patience=0, para se o modelo parar de evoluir
        device=0,
    )
    
    print("Treinamento concluido!")
    
    model.export(format="openvino")