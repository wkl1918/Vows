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

interface LanguageOption {
    code: string;
    label: string;
}

const LANGUAGE_OPTIONS: LanguageOption[] = [
    { code: 'zh', label: 'zh - 中文' },
    { code: 'en', label: 'en - 英文' },
    { code: 'ja', label: 'ja - 日文' },
    { code: 'ko', label: 'ko - 韩文' },
    { code: 'es', label: 'es - 西班牙语' },
    { code: 'fr', label: 'fr - 法语' },
    { code: 'de', label: 'de - 德语' },
    { code: 'ru', label: 'ru - 俄语' },
    { code: 'it', label: 'it - 意大利语' },
    { code: 'pt', label: 'pt - 葡萄牙语' },
    { code: 'ar', label: 'ar - 阿拉伯语' },
    { code: 'hi', label: 'hi - 印地语' },
    { code: 'th', label: 'th - 泰语' },
    { code: 'vi', label: 'vi - 越南语' },
    { code: 'tr', label: 'tr - 土耳其语' },
    { code: 'nl', label: 'nl - 荷兰语' },
    { code: 'pl', label: 'pl - 波兰语' },
    { code: 'id', label: 'id - 印尼语' },
    { code: 'ms', label: 'ms - 马来语' },
    { code: 'fa', label: 'fa - 波斯语' },
    { code: 'uk', label: 'uk - 乌克兰语' },
    { code: 'cs', label: 'cs - 捷克语' },
    { code: 'sk', label: 'sk - 斯洛伐克语' },
    { code: 'hu', label: 'hu - 匈牙利语' },
    { code: 'ro', label: 'ro - 罗马尼亚语' },
    { code: 'bg', label: 'bg - 保加利亚语' },
    { code: 'hr', label: 'hr - 克罗地亚语' },
    { code: 'sl', label: 'sl - 斯洛文尼亚语' },
    { code: 'sr', label: 'sr - 塞尔维亚语' },
    { code: 'da', label: 'da - 丹麦语' },
    { code: 'sv', label: 'sv - 瑞典语' },
    { code: 'no', label: 'no - 挪威语' },
    { code: 'fi', label: 'fi - 芬兰语' },
    { code: 'et', label: 'et - 爱沙尼亚语' },
    { code: 'lv', label: 'lv - 拉脱维亚语' },
    { code: 'lt', label: 'lt - 立陶宛语' },
    { code: 'el', label: 'el - 希腊语' },
    { code: 'he', label: 'he - 希伯来语' },
    { code: 'bn', label: 'bn - 孟加拉语' },
    { code: 'ta', label: 'ta - 泰米尔语' },
    { code: 'te', label: 'te - 泰卢固语' },
    { code: 'mr', label: 'mr - 马拉地语' },
    { code: 'gu', label: 'gu - 古吉拉特语' },
    { code: 'kn', label: 'kn - 卡纳达语' },
    { code: 'ml', label: 'ml - 马拉雅拉姆语' },
    { code: 'ur', label: 'ur - 乌尔都语' },
    { code: 'sw', label: 'sw - 斯瓦希里语' },
    { code: 'af', label: 'af - 南非语' },
    { code: 'fil', label: 'fil - 菲律宾语' },
    { code: 'ca', label: 'ca - 加泰罗尼亚语' },
];

function App() {
    const [task, setTask] = useState<TaskResponse | null>(null);
    const [uploading, setUploading] = useState(false);
    const [targetLanguage, setTargetLanguage] = useState<string>('zh');
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            console.log(`Uploading to ${API_URL}/upload?target_language=${targetLanguage}...`);
            const res = await axios.post(`${API_URL}/upload?target_language=${targetLanguage}`, formData, {
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
                    <div className="space-y-4">
                        <div className="bg-neutral-800 border border-neutral-700 rounded-xl p-4">
                            <label className="block text-sm text-neutral-300 mb-2">目标语言 (50选1)</label>
                            <select
                                className="w-full rounded-lg bg-neutral-900 border border-neutral-700 px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
                                value={targetLanguage}
                                onChange={(e) => setTargetLanguage(e.target.value)}
                                disabled={uploading}
                            >
                                {LANGUAGE_OPTIONS.map((option) => (
                                    <option key={option.code} value={option.code}>
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                        </div>

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
