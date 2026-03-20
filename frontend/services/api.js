import axios from "axios";

const API = "https://vocalseparatorai.onrender.com";  //http://127.0.0.1:5000/api for localhost

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await axios.post(`${API}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return res.data.job_id;
}

export async function uploadYouTube(url) {
  const res = await axios.post(`${API}/youtube`, {
    url: url
  });

  return res.data.job_id;
}

export async function getProgress(jobId) {
  const res = await axios.get(`${API}/progress/${jobId}`);
  return res.data;
}

export async function getResult(jobId) {
  const res = await axios.get(`${API}/result/${jobId}`);
  return res.data;
}