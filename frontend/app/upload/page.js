"use client";

import { useState, useEffect, useRef } from "react";

import {
UploadCloud,
FileMusic,
Wand2,
Download,
Mic,
Piano,
Play,
Pause
} from "lucide-react";

import { uploadFile,getProgress,getResult } from "../../services/api";

import { useJobStore } from "@/store/jobStore";


export default function UploadPage(){

const [file,setFile]=useState(null);

const [playing,setPlaying]=useState(null);

const audioRef=useRef(null);

const {uploadJob,startJob,setProgress,finishJob}=useJobStore();


useEffect(()=>{

if(!uploadJob?.id) return;

const interval=setInterval(async()=>{

const data=await getProgress(uploadJob.id);

setProgress("upload",data.progress);

if(data.progress===100){

const res=await getResult(uploadJob.id);

if(res.status==="done"){

finishJob("upload",res);

clearInterval(interval);

}

}

},2000);

return ()=>clearInterval(interval);

},[uploadJob?.id,setProgress,finishJob]);


const handleUpload=async()=>{

if(!file) return;

try{

const id=await uploadFile(file);

startJob(id,"upload");

}catch(e){

console.log(e);

}

};


const togglePlay=(url,type)=>{

if(playing===type){

audioRef.current.pause();

setPlaying(null);

return;

}

if(audioRef.current){

audioRef.current.pause();

}

audioRef.current=new Audio(url);

audioRef.current.play();

setPlaying(type);

};



return(

<div className="max-w-3xl mx-auto py-16">


{/* TITLE */}

<div className="text-center mb-12">

<h1 className="text-4xl font-bold text-gray-900">
Process Your Track
</h1>

<p className="mt-3 text-gray-500">
Upload your song and let AI separate vocals instantly.
</p>

</div>



{/* UPLOAD CARD */}

{!file && !uploadJob?.isProcessing && !uploadJob?.result &&(

<div className="bg-white rounded-3xl shadow-sm border p-10 text-center">

<div className="flex justify-center mb-6">

<div className="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center">

<UploadCloud size={36} className="text-red-500"/>

</div>

</div>


<h3 className="text-xl font-semibold text-gray-900">
Upload Your Song
</h3>

<p className="text-gray-500 mt-2">
Supports MP3, WAV, FLAC, M4A
</p>


<label className="mt-6 inline-block bg-red-500 text-white px-6 py-3 rounded-xl cursor-pointer hover:bg-red-600 transition">

Select File

<input
type="file"
hidden
onChange={(e)=>setFile(e.target.files[0])}
/>

</label>

</div>

)}



{/* FILE PREVIEW */}

{file && !uploadJob?.isProcessing && !uploadJob?.result &&(

<div className="mt-8 bg-white rounded-2xl border p-6">

<div className="flex items-center gap-4">

<FileMusic className="text-gray-500"/>

<div className="flex-1">

<p className="font-medium text-gray-900 truncate">
{file.name}
</p>

<p className="text-sm text-gray-400">
{(file.size/1024/1024).toFixed(1)} MB
</p>

</div>

</div>


<button

onClick={handleUpload}

className="mt-6 w-full bg-black text-white py-3 rounded-xl hover:opacity-90 transition flex items-center justify-center gap-2 cursor-pointer"
>

<Wand2 size={18}/>

Start Separation

</button>

</div>

)}



{/* PROGRESS */}

{uploadJob?.isProcessing &&(

<div className="mt-10 bg-white rounded-3xl shadow-sm border p-10 text-center">

<div className="relative w-40 h-40 mx-auto">

<div className="absolute inset-0 flex items-center justify-center text-2xl font-bold">

{uploadJob.progress}%

</div>


<svg className="w-40 h-40 transform -rotate-90">

<circle
cx="80"
cy="80"
r="70"
stroke="#eee"
strokeWidth="12"
fill="none"
/>

<circle
cx="80"
cy="80"
r="70"
stroke="#ef4444"
strokeWidth="12"
fill="none"
strokeDasharray={440}
strokeDashoffset={
440-(440*uploadJob.progress)/100
}
strokeLinecap="round"
/>

</svg>

</div>


<h3 className="mt-6 text-lg font-semibold text-gray-900">
Separating Vocals...
</h3>

<p className="text-gray-500">
AI processing your track
</p>

</div>

)}



{/* RESULTS */}

{uploadJob?.result &&(

<div className="mt-12 bg-white rounded-3xl shadow-sm border p-10 space-y-6">


{/* VOCALS */}

<div className="flex items-center justify-between p-5 border rounded-2xl">

<div className="flex items-center gap-4">

<Mic/>

<span className="font-medium">
Vocals
</span>

</div>


<div className="flex gap-5 items-center">


<button

onClick={()=>togglePlay(
uploadJob.result.vocals,
"vocals"
)}

className="text-green-600 cursor-pointer"
>

{playing==="vocals" ? <Pause/> : <Play/>}

</button>


<a

href={uploadJob.result.vocals}

download

className="text-red-500 cursor-pointer"
>

<Download/>

</a>

</div>

</div>



{/* INSTRUMENTAL */}

<div className="flex items-center justify-between p-5 border rounded-2xl">

<div className="flex items-center gap-4">

<Piano/>

<span className="font-medium">
Instrumental
</span>

</div>


<div className="flex gap-5 items-center">


<button

onClick={()=>togglePlay(
uploadJob.result.instrumental,
"instrumental"
)}

className="text-green-600 cursor-pointer"
>

{playing==="instrumental" ? <Pause/> : <Play/>}

</button>


<a

href={uploadJob.result.instrumental}

download

className="text-red-500 cursor-pointer"
>

<Download/>

</a>

</div>

</div>


</div>

)}



<div className="mt-20 text-center text-gray-400 text-sm">

© 2026 VocalSeparatorAI

</div>


</div>

);

}