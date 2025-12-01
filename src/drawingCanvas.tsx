import React, {
  useRef,
  useState,
  useEffect,
  forwardRef,
  useImperativeHandle,
} from "react";

export interface CanvasMaskRef {
  getYoloText: () => string;
  loadImage: (url: string) => void;
}
    // Types
    interface Point {
    x: number;
    y: number;
    }
    interface Shape {
    points: Point[];
    color: string;
    stroke: string;
    }
    

    const CanvasMaskExport = forwardRef<CanvasMaskRef>((props, ref) => {
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const [img, setImg] = useState<HTMLImageElement | null>(null);
    const [shapes, setShapes] = useState<Shape[]>([]);
    const [points, setPoints] = useState<Point[]>([]);
    const [drawingMode, setDrawingMode] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
    const [yoloText, setYoloText] = useState("");

    const rand255 = () => Math.floor(Math.random() * 256);

    // ✅ Expose functions to parent
    useImperativeHandle(ref, () => ({
        getYoloText: () => yoloText,
        loadImage: (url: string) => loadImage(url),
    }));

    useEffect(() => {
        drawAll();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [img, shapes, points, drawingMode, selectedIndex]);

    function getCtx(): CanvasRenderingContext2D | null {
        const canvas = canvasRef.current;
        if (!canvas) return null;
        return canvas.getContext("2d");
    }

    function drawAll() {
        const canvas = canvasRef.current;
        const ctx = getCtx();
        if (!ctx || !canvas) return;

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (img) ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

        shapes.forEach((shape, idx) => {
        ctx.fillStyle = shape.color;
        ctx.strokeStyle = shape.stroke;
        ctx.lineWidth = 2;

        ctx.beginPath();
        ctx.moveTo(shape.points[0].x, shape.points[0].y);
        for (let i = 1; i < shape.points.length; i++)
            ctx.lineTo(shape.points[i].x, shape.points[i].y);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        if (idx === selectedIndex) {
            ctx.save();
            ctx.strokeStyle = "#ffea00";
            ctx.lineWidth = 3;
            ctx.stroke();
            ctx.restore();
        }

        ctx.fillStyle = "#ff0000";
        for (const p of shape.points) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
            ctx.fill();
        }
        });

        if (drawingMode && points.length > 0) {
        ctx.fillStyle = "#ff0000";
        ctx.strokeStyle = "rgba(0,0,0,0.5)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x, points[i].y);
        ctx.stroke();
        for (const p of points) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
            ctx.fill();
        }
        }
    }

    // ✅ Load image from URL
    function loadImage(url: string) {
        const image = new Image();
        image.crossOrigin = "anonymous"; // allow external images
        image.onload = () => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        // 🔹 Scale image to max width
        const maxWidth = 800;
        let scale = 1;
        if (image.width > maxWidth) {
            scale = maxWidth / image.width;
        }
        const newWidth = image.width * scale;
        const newHeight = image.height * scale;

        canvas.width = newWidth;
        canvas.height = newHeight;

        setShapes([]);
        setPoints([]);
        setDrawingMode(false);
        setSelectedIndex(null);
        setYoloText("");
        setImg(image);
        };
        image.src = url;
    }

    function toCanvasCoords(clientX: number, clientY: number): Point {
        const canvas = canvasRef.current!;
        const rect = canvas.getBoundingClientRect();
        const x = Math.round((clientX - rect.left) * (canvas.width / rect.width));
        const y = Math.round((clientY - rect.top) * (canvas.height / rect.height));
        return { x, y };
    }

    function onCanvasClick(e: React.MouseEvent<HTMLCanvasElement>) {
        if (!img) return;
        const p = toCanvasCoords(e.clientX, e.clientY);

        if (drawingMode) {
        setPoints((prev) => [...prev, p]);
        return;
        }

        const ctx = getCtx();
        if (!ctx) return;
        let found: number | null = null;
        for (let i = 0; i < shapes.length; i++) {
        const shape = shapes[i];
        ctx.beginPath();
        ctx.moveTo(shape.points[0].x, shape.points[0].y);
        for (let j = 1; j < shape.points.length; j++)
            ctx.lineTo(shape.points[j].x, shape.points[j].y);
        ctx.closePath();
        if (ctx.isPointInPath(p.x, p.y)) {
            found = i;
            break;
        }
        }
        setSelectedIndex(found);
    }

    function startDrawing() {
        setDrawingMode(true);
        setPoints([]);
        setSelectedIndex(null);
    }

    function finishDrawing() {
        if (!drawingMode) return;
        if (points.length < 3) return alert("Need at least 3 points");

        const color = `rgba(${rand255()},${rand255()},${rand255()},0.35)`;
        const newShape: Shape = { points: points.slice(), color, stroke: "#2563eb" };
        setShapes((s) => [...s, newShape]);

        const canvas = canvasRef.current!;
        const w = canvas.width,
        h = canvas.height;
        const yoloClass = 0;
        const coords = points
        .map((p) => `${(p.x / w).toFixed(6)} ${(p.y / h).toFixed(6)}`)
        .join(" ");
        const line = `${yoloClass} ${coords}`;
        // setYoloText((t) => (t ? t + "\n" + line : line));
        setYoloText((t) => (t ? t + " ;" + line : line));


        setPoints([]);
        setDrawingMode(false);
    }

    function deleteSelected() {
        if (selectedIndex === null) return alert("Select a shape first");
        setShapes((s) => s.filter((_, i) => i !== selectedIndex));
        setYoloText((t) => {
        const lines = t.split(" ;");
        lines.splice(selectedIndex, 1);
        return lines.join(";");
        });

        setSelectedIndex(null);
    }

    return (
        <div className="max-w-4xl mx-auto p-4">
        <div className="flex gap-2 items-center mb-3">
            <button
            onClick={startDrawing}
            className="px-3 py-1 bg-sky-600 text-white rounded"
            >
            Draw
            </button>
            <button
            onClick={finishDrawing}
            className="px-3 py-1 bg-green-600 text-white rounded"
            >
            Finish
            </button>
            <button
            onClick={deleteSelected}
            className="px-3 py-1 bg-red-600 text-white rounded"
            >
            Delete
            </button>
        </div>
        <div className="border border-gray-300 inline-block">
            <canvas
            ref={canvasRef}
            onClick={onCanvasClick}
            style={{ cursor: img ? "crosshair" : "default", display: "block" }}
            />
        </div>
        </div>
    );
    });

    export default CanvasMaskExport;
