"use client";

import { useState,useEffect,useRef } from "react";

import {
Link as LinkIcon,
Wand2,
Download,
Mic,
Piano,
Play,
Pause
} from "lucide-react";

import { uploadYouTube,getProgress,getResult } from "../../services/api";

import { useJobStore } from "@/store/jobStore";

export default function ConverterPage(){

const [url,setUrl]=useState("");
const [loading,setLoading]=useState(false);

const [playing,setPlaying]=useState(null);
const [currentTime,setCurrentTime]=useState(0);
const [duration,setDuration]=useState(0);

const audioRef=useRef(null);

const {youtubeJob,startJob,setProgress,finishJob}=useJobStore();

useEffect(()=>{

if(!youtubeJob?.id) return;

const interval=setInterval(async()=>{

const data=await getProgress(youtubeJob.id);

setProgress("youtube",data.progress);

if(data.progress===100){

const res=await getResult(youtubeJob.id);

if(res.status==="done"){

finishJob("youtube",res);

clearInterval(interval);

}

}

},2000);

return ()=>clearInterval(interval);

},[youtubeJob?.id,setProgress,finishJob]);


const handleConvert=async()=>{

if(!url) return;

setLoading(true);

const id=await uploadYouTube(url);

startJob(id,"youtube");

setLoading(false);

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

audioRef.current.onloadedmetadata=()=>{

setDuration(audioRef.current.duration);

};

audioRef.current.ontimeupdate=()=>{

setCurrentTime(audioRef.current.currentTime);

};

setPlaying(type);

};


const formatTime=(t)=>{

if(!t) return "0:00";

const min=Math.floor(t/60);

const sec=Math.floor(t%60);

return min+":"+(sec<10?"0":"")+sec;

};


const seek=(e)=>{

const value=e.target.value;

audioRef.current.currentTime=value;

setCurrentTime(value);

};


return(

<div className="max-w-3xl mx-auto py-16">

<div className="text-center mb-12">

<h1 className="text-4xl font-bold text-gray-900">
Convert YouTube to Tracks
</h1>

<p className="mt-4 text-gray-500 text-lg">
Paste a YouTube link below to separate vocals and music instantly.
</p>

</div>


{!youtubeJob?.result &&(

<div className="bg-white rounded-3xl shadow-sm border p-10">

<div className="relative">

<LinkIcon className="absolute left-4 top-1/2 text-gray-400"/>

<input
type="text"
placeholder="Paste YouTube URL"
className="w-full pl-12 py-4 border rounded-2xl"
value={url}
onChange={(e)=>setUrl(e.target.value)}
/>

</div>


<button
onClick={handleConvert}
className="mt-8 w-full bg-red-500 text-white py-4 rounded-2xl flex justify-center gap-2"
>

<Wand2/>

{loading?"Processing":"Convert"}

</button>

</div>

)}


{youtubeJob?.result &&(

<div className="mt-12 bg-white rounded-3xl border p-10 space-y-6">

<div className="flex justify-between p-5 border rounded-2xl">

<div className="flex gap-4">

<Mic/>

<span>Vocals</span>

</div>

<div className="flex gap-5">

<button onClick={()=>togglePlay(
youtubeJob.result.vocals,
"vocals"
)}>

{playing==="vocals"?<Pause/>:<Play/>}

</button>

<a href={youtubeJob.result.vocals} download>

<Download/>

</a>

</div>

</div>


<div className="flex justify-between p-5 border rounded-2xl">

<div className="flex gap-4">

<Piano/>

<span>Instrumental</span>

</div>

<div className="flex gap-5">

<button onClick={()=>togglePlay(
youtubeJob.result.instrumental,
"instrumental"
)}>

{playing==="instrumental"?<Pause/>:<Play/>}

</button>

<a href={youtubeJob.result.instrumental} download>

<Download/>

</a>

</div>

</div>


{playing &&(

<div className="mt-8 border rounded-2xl p-6">

<p className="font-medium mb-3">

Now Playing: {playing}

</p>

<input
type="range"
min="0"
max={duration}
value={currentTime}
onChange={seek}
className="w-full"
/>

<div className="flex justify-between text-sm text-gray-500 mt-2">

<span>{formatTime(currentTime)}</span>

<span>{formatTime(duration)}</span>

</div>

</div>

)}

</div>

)}

</div>

);

}