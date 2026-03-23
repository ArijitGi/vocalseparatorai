const API="https://vocalseparatorai.onrender.com/api";


export const uploadFile = async(file)=>{

const formData=new FormData();

formData.append("file",file);

const res=await fetch(`${API}/upload`,{

method:"POST",

body:formData

});

const data=await res.json();

return data.job_id;

};



export const uploadYouTube = async(url)=>{

const res=await fetch(`${API}/youtube`,{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({url})

});

const data=await res.json();

return data.job_id;

};



export const getProgress = async(id)=>{

const res=await fetch(`${API}/progress/${id}`);

return res.json();

};



export const getResult = async(id)=>{

const res=await fetch(`${API}/result/${id}`);

return res.json();

};