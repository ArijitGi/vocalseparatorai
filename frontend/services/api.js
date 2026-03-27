const API = "https://vocalseparatorai.onrender.com/api";

export const uploadFile = async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    
    try {
        const res = await fetch(`${API}/upload`, {
            method: "POST",
            body: formData,
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.error || "Upload failed");
        }
        
        const data = await res.json();
        return data.job_id;
    } catch (error) {
        console.error("Upload error:", error);
        throw error;
    }
};

export const uploadYouTube = async (url) => {
    try {
        const res = await fetch(`${API}/youtube`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ url }),
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.error || "YouTube conversion failed");
        }
        
        const data = await res.json();
        return data.job_id;
    } catch (error) {
        console.error("YouTube error:", error);
        throw error;
    }
};

export const getProgress = async (id) => {
    try {
        const res = await fetch(`${API}/progress/${id}`);
        
        if (!res.ok) {
            throw new Error("Failed to get progress");
        }
        
        return await res.json();
    } catch (error) {
        console.error("Progress error:", error);
        return { progress: 0, elapsed: 0, estimate: 300 };
    }
};

export const getResult = async (id) => {
    try {
        const res = await fetch(`${API}/result/${id}`);
        
        if (!res.ok) {
            throw new Error("Failed to get result");
        }
        
        return await res.json();
    } catch (error) {
        console.error("Result error:", error);
        return { status: "error" };
    }
};