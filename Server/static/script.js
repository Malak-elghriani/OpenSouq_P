let latitude = null;
let longitude = null;

const modal = document.getElementById("mapModal");
const openMapBtn = document.getElementById("openMap");
const closeModal = document.getElementById("closeModal");

openMapBtn.onclick = function(){
    modal.style.display = "block";
    initMap();

    setTimeout(function(){
        map.invalidateSize();
    },100);
};

let map;
let marker;

function initMap(){

    if(map) return;

    map = L.map('map').setView([32.8872, 13.1913], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution:'© OpenStreetMap'
    }).addTo(map);

    map.on('click', function(e){

        latitude = e.latlng.lat;
        longitude = e.latlng.lng;

        if(marker){
            map.removeLayer(marker);
        }

        marker = L.marker([latitude, longitude]).addTo(map);

        document.getElementById("result").innerText =
            "Location Selected";
    });

}

closeModal.onclick = function(){
    modal.style.display = "none";
};

window.onclick = function(event){

    if(event.target === modal){
        modal.style.display = "none";
    }

};

document.getElementById("priceForm").addEventListener("submit",function(e){

e.preventDefault();

const bedrooms = parseInt(document.getElementById("bedrooms").value);
const bathrooms = parseInt(document.getElementById("bathrooms").value);
const surface_area = parseFloat(document.getElementById("surface_area").value);

fetch("/estimate_price",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({
bedrooms:bedrooms,
bathrooms:bathrooms,
surface_area:surface_area,
latitude:latitude,
longitude:longitude
})

})
.then(res=>res.json())
.then(data=>{

document.getElementById("result").innerText =
"Estimated Price: $" + data.estimated_price;

});

});