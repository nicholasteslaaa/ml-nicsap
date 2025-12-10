import cv2, numpy as np,sys


class movementDetectionModel:
    def __init__(self,video_path,frame_gap = 5,brightness = 6):
        if (video_path != None):
            self.video = self.preparingVideo(video_path,frame_gap,brightness = brightness)[1:]
            self.total_frame = len(self.video)
        self.frame_gap = frame_gap
        self.preparingProgress = 0
        self.cleaned_position_log = []
        self.box = ()
        
    def draw_grid_difference(self,prev_frame, curr_frame, grid_size=60, threshold = 50,show_grid = False):
        gray_prev = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        gray_curr = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray_curr, gray_prev)
        diff_norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
        overlay = curr_frame.copy()
        h, w = diff.shape
               
        rawPosLog = []
        black_threshold = 50  # <-- adjust as needed
        for y in range(0, h, grid_size):
            for x in range(0, w, grid_size):
                y_end, x_end = min(y + grid_size, h), min(x + grid_size, w)
                
                # movement intensity (difference)
                cell_diff = np.mean(diff_norm[y:y_end, x:x_end])
                intensity = int(np.clip(cell_diff, 0, 255))

                # brightness check (is current frame pixel black)
                avg_pixel = np.mean(gray_curr[y:y_end, x:x_end])

                # ✅ Only count movement if intensity is high AND pixel is black
                if intensity > threshold and avg_pixel < black_threshold:
                    rawPosLog.append((x, y))
                    
        self.cleaned_position_log = self.cleaningPosLog(rawPosLog)        

        self.box = ()
        if self.cleaned_position_log:
            for position in self.cleaned_position_log:
                x,y = position[0], position[1]
                x_end,y_end = x+grid_size, y+grid_size
                cv2.rectangle(overlay, (x, y), (x_end, y_end), (0, 255, 0), -1)
            
            min_x = self.cleaned_position_log[0][0]
            min_y = self.cleaned_position_log[0][1]
            max_x = min_x+grid_size
            max_y = min_y+grid_size
            
            for x,y in self.cleaned_position_log:
                if (x < min_x): min_x = x
                if (y < min_y): min_y = y
                if (x+grid_size > max_x): max_x = x+grid_size
                if (y+grid_size > max_y): max_y = y+grid_size
            
            self.box = (min_x,min_y,max_x,max_y)
            
            cv2.rectangle(overlay, (min_x, min_y), (max_x, max_y), (0, 255, 255), 3)  # yellow rectangle

        result = cv2.addWeighted(overlay, 0.5, curr_frame, 0.5, 0)

        if show_grid:
            for y in range(0, h, grid_size):
                cv2.line(result, (0, y), (w, y), (0, 0, 255), 1)
            for x in range(0, w, grid_size):
                cv2.line(result, (x, 0), (x, h), (0, 0, 255), 1)
                
        return result
    
    def cleaningPosLog(self, posLog:list, threshold:float = 20):
        if not posLog:
            return posLog

        clusters = []  # list of clusters (each cluster is a list of points)

        for point in posLog:
            added = False

            # try to assign point into existing cluster
            for cluster in clusters:
                for member in cluster:
                    if self.euclidDistance(point, member) <= threshold:
                        cluster.append(point)
                        added = True
                        break
                if added:
                    break

            # if not added, create new cluster
            if not added:
                clusters.append([point])

        # Select the cluster with the most members
        clusters.sort(key=lambda c: len(c), reverse=True)
        best_cluster = clusters[0]

        return best_cluster

    
    def euclidDistance(self,positionA:tuple[int,int],positionB:tuple[int,int]):
        return np.sqrt((positionB[0]-positionA[0])**2 + (positionB[1]-positionA[1])**2)


    def preparingVideo(self,video_path,step=20,brightness = 6)->list:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print("Error opening video")
            exit()

        selected_frames = []

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        for frame_index in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)  # jump to frame
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.convertScaleAbs(frame,alpha=brightness)
            selected_frames.append(frame)
            self.progress_bar(frame_index+1,total_frames,message="🎬 Preparing Video ")
            
            self.preparingProgress = frame_index / total_frames
        cap.release()
        
        return selected_frames
    
    def progress_bar(self,progress, total,message="",bar_length=40):
        fraction = progress / total
        arrow = int(fraction * bar_length) * '='
        padding = (bar_length - len(arrow)) * '-'

        bar = f"{message} [{arrow}>{padding}] {int(fraction * 100)}%"

        sys.stdout.write("\r" + bar)
        sys.stdout.flush()

if __name__ == "__main__":
    videos_path = [
        r"E:\data datathon\RAM video\A4_Hari 10.mp4",
        r"E:\data datathon\drive-download-20250625T145832Z-1-004\B3_Hari 10.mp4",
        r"E:\data datathon\drive-download-20250625T145832Z-1-004\C1_Hari 10.mp4",
        r"E:\data datathon\drive-download-20250625T145832Z-1-004\C4_Hari 10.mp4",
        r"C:\Users\zrota\Videos\A1_Hari 10.mp4"
        ]

    md = movementDetectionModel(videos_path[0])
        
    print(f"Total selected frames: {len(md.video)}")
    # ✅ Display frames
    showGrid = False
    for frameIdx in range(len(md.video)-1):
        curr_frame = md.video[frameIdx+1]
        prev_frame = md.video[frameIdx]
        result =  md.draw_grid_difference(prev_frame,curr_frame,grid_size=10,threshold=80,show_grid=showGrid)

        cv2.imshow("Selected Frames",result)

        if cv2.waitKey(10) & 0xFF == ord('g'):
            showGrid = not showGrid
        if cv2.waitKey(10) & 0xFF == ord('q'):
            print("🛑 Video stopped by user.")
            break

    cv2.destroyAllWindows()
