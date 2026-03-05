import { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, FileAudio, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import clsx from 'clsx';

// API Base URL (Direct connection to backend to avoid Proxy issues)
const API_URL = 'http://127.0.0.1:8000/api/v1/tasks';

interface TaskResponse {
    id: string;
    filename: string;
    status: 'queued' | 'processing' | 'completed' | 'failed';
    progress: number;
    message: string;
}

function App() {
    const [task, setTask] = useState<TaskResponse | null>(null);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('target_language', 'zh'); // Default to Chinese

        try {
            console.log(`Uploading to ${API_URL}/upload...`);
            const res = await axios.post(`${API_URL}/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            console.log("Upload success:", res.data);
            setTask(res.data);
            pollTaskStatus(res.data.id);
        } catch (error: any) {
            console.error("Upload failed", error);
            alert(`Upload failed: ${error.message || "Unknown error"}`);
        } finally {
            setUploading(false);
        }
    };

    const pollTaskStatus = (taskId: string) => {
        const interval = setInterval(async () => {
            try {
                const res = await axios.get(`${API_URL}/${taskId}`);
                setTask(res.data);
                
                if (['completed', 'failed'].includes(res.data.status)) {
                    clearInterval(interval);
                }
            } catch (error) {
                console.error("Polling error", error);
                clearInterval(interval);
            }
        }, 1000);
    };

    return (
        <div className="min-h-screen bg-neutral-900 text-white p-8 font-sans">
            <header className="max-w-4xl mx-auto mb-12 flex items-center gap-3">
                <div className="w-10 h-10 bg-indigo-500 rounded-lg flex items-center justify-center">
                    <FileAudio className="text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">VoxFlow Studio</h1>
                    <p className="text-neutral-400">Local AI Dubbing & Translation</p>
                </div>
            </header>

            <main className="max-w-xl mx-auto">
                {/* Upload Zone */}
                {!task && (
                    <div 
                        className={clsx(
                            "border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer",
                            uploading ? "border-indigo-500 bg-indigo-500/10" : "border-neutral-700 hover:border-indigo-500 hover:bg-neutral-800"
                        )}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <input 
                            type="file" 
                            className="hidden" 
                            ref={fileInputRef} 
                            onChange={handleFileUpload}
                            accept="video/*,audio/*"
                        />
                        <div className="flex flex-col items-center gap-4">
                            {uploading ? (
                                <Loader2 className="w-12 h-12 text-indigo-500 animate-spin" />
                            ) : (
                                <Upload className="w-12 h-12 text-neutral-500" />
                            )}
                            <div className="text-lg font-medium">
                                {uploading ? "Uploading..." : "Click to Upload Video/Audio"}
                            </div>
                            <p className="text-neutral-500 text-sm">Supports MP4, WAV, MP3</p>
                        </div>
                    </div>
                )}

                {/* Task Status Card */}
                {task && (
                    <div className="bg-neutral-800 rounded-xl p-6 border border-neutral-700 shadow-xl">
                        <div className="flex justify-between items-start mb-6">
                            <div>
                                <h2 className="text-xl font-semibold">{task.filename}</h2>
                                <span className={clsx(
                                    "px-2 py-0.5 rounded text-xs font-medium uppercase tracking-wider mt-1 inline-block",
                                    task.status === 'completed' && "bg-green-500/20 text-green-400",
                                    task.status === 'processing' && "bg-blue-500/20 text-blue-400",
                                    task.status === 'failed' && "bg-red-500/20 text-red-400",
                                    task.status === 'queued' && "bg-yellow-500/20 text-yellow-400",
                                )}>
                                    {task.status}
                                </span>
                            </div>
                            {task.status === 'completed' && <CheckCircle className="text-green-500 w-6 h-6" />}
                            {task.status === 'failed' && <AlertCircle className="text-red-500 w-6 h-6" />}
                        </div>

                        {/* Progress Bar */}
                        <div className="w-full bg-neutral-700 h-2 rounded-full overflow-hidden mb-4">
                            <div 
                                className="bg-indigo-500 h-full transition-all duration-500 ease-out"
                                style={{ width: `${task.progress}%` }}
                            />
                        </div>

                        <div className="flex justify-between text-sm text-neutral-400 font-mono">
                            <span>{task.message}</span>
                            <span>{task.progress}%</span>
                        </div>
                        
                        {task.status === 'completed' && (
                            <div className="mt-6 pt-6 border-t border-neutral-700">
                                <button onClick={() => setTask(null)} className="text-sm text-neutral-500 hover:text-white underline">
                                    Process another file
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    )
}

export default App
