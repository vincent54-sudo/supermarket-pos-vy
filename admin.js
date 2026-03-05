const API_URL = "https://supermarket-pos-bh4k.onrender.com";

document.getElementById("productForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    // 1. Collect data from the form
    const productData = {
        id: document.getElementById("pId").value,
        name: document.getElementById("pName").value,
        category: "General", 
        stock: parseInt(document.getElementById("pStock").value),
        price: parseFloat(document.getElementById("pPrice").value),
        barcode: document.getElementById("pBarcode").value
    };

    // 2. Send to Backend
    try {
        const response = await fetch(`${API_URL}/api/products`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                // You must be logged in to get this token
                "Authorization": `Bearer ${localStorage.getItem("token")}` 
            },
            body: JSON.stringify(productData)
        });

        if (response.ok) {
            alert("Product added to Database successfully!");
            location.reload(); // Refresh to see changes
        } else {
            const error = await response.json();
            alert("Error: " + error.detail);
        }
    } catch (err) {
        alert("Backend is offline!");
    }
});
const socket = new WebSocket("wss://supermarket-pos-bh4k.onrender.com/ws");
socket.onmessage = function(event) {
    console.log("Real-time update:", event.data);
    // This will trigger every time processSale runs on the POS side
    showNotification("New Sale Completed!"); 
    loadInventory(); // Function to refresh your table
};