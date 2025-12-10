import cv2, numpy as np,random,os
from movementDetector import movementDetectionModel
from randomForest import NoiseFilter
from datetime import datetime

class RAM_Analysis:
    def __init__(self,dataset:str):
        self.rf = NoiseFilter(dataset)
        self.rf.train()
        self.progress_video = -1
    
    def draw_random_shape(self,frame):
        h, w, _ = frame.shape
        
        color = (0,0,0)

        # random thickness (use -1 for filled)
        thickness = random.choice([-1, 2, 3])

        shape_type = random.choice([
            "circle",
            "rectangle",
            "triangle",
            "ellipse"
        ])

        # random points
        x1, y1 = random.randint(0, w), random.randint(0, h)
        x2, y2 = random.randint(0, w), random.randint(0, h)

        if shape_type == "circle":
            radius = random.randint(5, 80)
            cv2.circle(frame, (x1, y1), radius, color, thickness)

        elif shape_type == "rectangle":
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        elif shape_type == "triangle":
            pts = np.array([
                [random.randint(0, w), random.randint(0, h)],
                [random.randint(0, w), random.randint(0, h)],
                [random.randint(0, w), random.randint(0, h)],
            ])
            cv2.drawContours(frame, [pts], 0, color, thickness)

        elif shape_type == "ellipse":
            axes = (random.randint(10, 80), random.randint(10, 80))
            angle = random.randint(0, 180)
            cv2.ellipse(frame, (x1, y1), axes, angle, 0, 360, color, thickness)

        return frame

    def parse_yolo_polygon(self,mask_string, img_w, img_h):
        """
        Convert YOLO polygon string to list of numpy polygons (pixel coordinates)
        """
        polygons = []
        
        for poly in mask_string.split(";"):
            poly = poly.strip()
            if not poly:
                continue
                
            values = poly.split()
            coords = list(map(float, values[1:]))

            points = []
            for i in range(0, len(coords), 2):
                x = int(coords[i] * img_w)
                y = int(coords[i+1] * img_h)
                points.append((x, y))

            polygons.append(np.array(points, dtype=np.int32))

        return polygons


    def is_bbox_center_inside_mask(self,min_x, min_y, max_x, max_y, mask_string, img_w, img_h):
        cx = int((min_x + max_x) / 2)
        cy = int((min_y + max_y) / 2)

        values = mask_string.split()
        coords = list(map(float, values[1:]))

        points = []
        for i in range(0, len(coords), 2):
            x = int(coords[i] * img_w)
            y = int(coords[i+1] * img_h)
            points.append((x, y))

        polygon = np.array(points, dtype=np.int32)

        return cv2.pointPolygonTest(polygon, (cx, cy), False) >= 0

    def get_polygon_center(self,mask_str, img_w, img_h):
        values = mask_str.split()
        coords = list(map(float, values[1:]))  # skip class id
        points = np.array([[coords[i] * img_w, coords[i+1] * img_h] 
                        for i in range(0, len(coords), 2)])
        
        # centroid calculation
        M = cv2.moments(points.astype(np.int32))
        if M["m00"] == 0:
            return points.mean(axis=0)  # fallback if degenerate polygon
        cx = M["m10"] / M["m00"]
        cy = M["m01"] / M["m00"]
        return np.array([cx, cy])

    def getIsInsideArm(self,bounding_box, overlay_mask, h, w):
        min_x, min_y, max_x, max_y = bounding_box
        for mask in overlay_mask:
            if self.is_bbox_center_inside_mask(min_x, min_y, max_x, max_y, mask, w, h):
                return mask
        return False


    def draw_yolo_mask(self,frame, mask_data, armLog, alpha=0.4):
        h, w = frame.shape[:2]
        overlay = frame.copy()
        
        for poly in mask_data:
            maskCenter = self.get_polygon_center(poly,w,h)
            
            poly_clean = poly.strip()
            if not poly_clean:
                continue
            
            # ✅ Reset color for EACH polygon
            color = (255, 0, 0)  # default = blue

            if poly_clean in armLog:
                if armLog[poly_clean] == 1:
                    color = (0, 255, 0)   # green = visited once
                elif armLog[poly_clean] > 1:
                    color = (0, 0, 255)   # red = revisited

            values = poly_clean.split()
            coords = list(map(float, values[1:]))

            points = []
            for i in range(0, len(coords), 2):
                x = int(coords[i] * w)
                y = int(coords[i+1] * h)
                points.append([x, y])
        

            points = np.array([points], dtype=np.int32)
            cv2.fillPoly(overlay, points, color)
            cv2.circle(overlay,(int(maskCenter[0]),int(maskCenter[1])),3,(0,0,255),-1)
            
        return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    def process_video(self,videos_path:str,overlay_mask:list[str]):
        md = movementDetectionModel(videos_path,frame_gap=5)
        totalFrame = len(md.video)
        
        original_filename = os.path.basename(videos_path)
        
        # --- VideoWriter setup ---
        filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".webm"
        output_dir = os.path.abspath("../public/output")
        os.makedirs(output_dir, exist_ok=True)

        finalPath = os.path.join(output_dir, filename)
        
        fourcc = cv2.VideoWriter_fourcc(*'VP80')
        h, w = md.video[0].shape[:2]             # get height and width from first frame
        out = cv2.VideoWriter(finalPath, fourcc, md.frame_gap, (w, h))  # fps = 30, adjust if needed
        # -------------------------
        
        armLog = {}
        lastArm = None
        for frameIdx in range(totalFrame-1):            
            curr_frame = md.video[frameIdx+1]
            prev_frame = md.video[frameIdx]
            curr_frame = md.draw_grid_difference(prev_frame,curr_frame,grid_size=10,threshold=80)
            if (len(md.box) > 0):
                curr_frame = cv2.rectangle(curr_frame,(md.box[0],md.box[1]),(md.box[2],md.box[3]),(0,255,255),3)
                pred, prob = self.rf.predict_box(md.box[0],md.box[1],md.box[2],md.box[3])
                label = "Noise" if pred == 0 else "Valid"
                color = (0,255,0) if label == "Valid" else (0,0,255)
                
                cv2.putText(curr_frame, f"Prediction: {label} {prob[pred]*100}%", (50,50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA)
                
                h,w = curr_frame.shape[:2]
                inside = self.getIsInsideArm(md.box,overlay_mask,h,w)
                if (label == "Valid"):
                    if (inside != False):
                        cx = (md.box[0] + md.box[2])/2
                        cy = (md.box[1] + md.box[3])/2
                        maskCenter = self.get_polygon_center(inside,w,h)
                        distance_to_center = md.euclidDistance((cx,cy),(int(maskCenter[0]),int(maskCenter[1])))/100
                        print(f"Distance: {distance_to_center}")
                        if (lastArm != inside and distance_to_center <= 0.5):
                            if (inside not in armLog):
                                armLog[inside] = 1
                            else:
                                armLog[inside] += 1
                            lastArm = inside
                cv2.putText(curr_frame, f"Prediction: {label} {prob[pred]*100}%, Status: {inside != False}", (md.box[0],md.box[1]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA)
    
                
            
            right = len(armLog)
            wrong = 0
            for i in list(armLog.values()):
                print(i)
                if (i > 1):
                    wrong += i-1
                
            # print(f"right: {right} wrong: {wrong}")
            cv2.putText(curr_frame, f"{original_filename}", (50,100), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2, cv2.LINE_AA)
            cv2.putText(curr_frame, f"right: {right}", (50,150), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2, cv2.LINE_AA)
            cv2.putText(curr_frame, f"wrong: {wrong}", (50,200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 2, cv2.LINE_AA)
            
            curr_frame = self.draw_yolo_mask(curr_frame,overlay_mask,armLog)

            # --- write frame to video ---
            self.progress_video = int((frameIdx/totalFrame)*100)
            # print(f"video progress: {self.progress_video}%")
            md.progress_bar(frameIdx+1,totalFrame,message=f"Right: {right}, Wrong: {wrong}")
            out.write(curr_frame)
        
        self.progress_video = -1
        out.release()
        cv2.destroyAllWindows()
        
if __name__ == '__main__':
    videos_path = [
        r"E:\data datathon\RAM video\A1_Hari 10.mp4",
        r"E:\data datathon\RAM video\A2_Hari 10.mp4",
        r"E:\data datathon\RAM video\A4_Hari 10.mp4",
        r"E:\data datathon\RAM video\B1_Hari 10.mp4",
        r"E:\data datathon\RAM video\B3_Hari 10.mp4",
        r"E:\data datathon\RAM video\C1_Hari 10.mp4",
        r"E:\data datathon\RAM video\C4_Hari 10.mp4",
    ]

    overlay_mask = [
        "0 0.548750 0.060000 0.591250 0.060000 0.583750 0.397778 0.538750 0.400000",
        "0 0.592500 0.400000 0.736250 0.177778 0.767500 0.217778 0.617500 0.442222",
        "0 0.621250 0.464444 0.835000 0.484444 0.840000 0.551111 0.623750 0.524444",
        "0 0.618750 0.551111 0.772500 0.840000 0.743750 0.893333 0.591250 0.604444",
        "0 0.367500 0.853333 0.338750 0.788889 0.511250 0.535556 0.535000 0.584444",
        "0 0.543750 0.593333 0.571250 0.593333 0.570000 0.993333 0.530000 0.993333",
        "0 0.510000 0.526667 0.286250 0.504444 0.291250 0.433333 0.510000 0.466667",
        "0 0.371250 0.186667 0.401250 0.151111 0.527500 0.393333 0.505000 0.457778",
    ]
    # RA = RAM_Analysis("merged_classification.csv")
    # RA.process_video(videos_path[0],overlay_mask)
    # Directory to save frames
    output_dir = "evaluationData"
    os.makedirs(output_dir, exist_ok=True)
    
    RA = RAM_Analysis("merged_classification.csv")
    for inputVidIdx in range(len(videos_path)):
        RA.process_video(videos_path[inputVidIdx],overlay_mask)