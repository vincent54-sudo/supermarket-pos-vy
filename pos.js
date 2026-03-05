// 1. GLOBAL VARIABLES (Always at the top)
let cartTotal = 0; 

// 2. THE BRAIN (Verification)
async function fetchProduct(identifier) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/barcode/${identifier}`);
        const product = await response.json();

        if (product && product.name) {
            addToTable(product);
        } else {
            alert("Product not found in Database!");
        }
    } catch (error) {
        alert("Backend Server is Offline!");
    }
}

// 3. THE UI (Updating the table and total)
function addToTable(product) {
    const tableBody = document.querySelector("#cartTable tbody");
    const totalDisplay = document.getElementById("grandTotal");
    
    const row = `
        <tr>
            <td>${product.name}</td>
            <td>$${product.price.toFixed(2)}</td>
            <td>1</td>
            <td>Success</td>
        </tr>
    `;
    tableBody.innerHTML += row;

    // Update the math
    cartTotal += product.price;
    if (totalDisplay) {
        totalDisplay.innerText = `Total: $${cartTotal.toFixed(2)}`;
    }
}

// 4. TRIGGERS (Button clicks and scanners)
function onScanSuccess(decodedText) {
    fetchProduct(decodedText); 
}

// Manual Input Trigger
const addBtn = document.getElementById("addBtn");
if (addBtn) {
    addBtn.addEventListener("click", (e) => {
        e.preventDefault();
        const manualInput = document.getElementById("itemId").value;
        if (manualInput) {
            fetchProduct(manualInput); 
            document.getElementById("itemId").value = ""; 
        }
    });
}

// Checkout Button Trigger
const checkoutBtn = document.getElementById("checkoutBtn");
if (checkoutBtn) {
    checkoutBtn.addEventListener("click", async () => {
        if (cartTotal === 0) return alert("Cart is empty!");

        // 1. Ask the backend to record the sale
        // For simplicity, we'll process the last scanned item. 
        // (In a full app, you'd send the whole list)
        alert(`Finalizing Sale: $${cartTotal.toFixed(2)}`);

        // 2. Clear the UI for the next customer
        document.querySelector("#cartTable tbody").innerHTML = "";
        cartTotal = 0;
        document.getElementById("grandTotal").innerText = "Total: $0.00";
        
        console.log("Sale finalized and UI reset.");
    });
}

// 5. CAMERA START (Always at the very bottom)
const html5QrCode = new Html5Qrcode("reader");
const config = { fps: 10, qrbox: { width: 250, height: 250 } };

html5QrCode.start(
    { facingMode: "environment" }, 
    config, 
    onScanSuccess
).catch(err => {
    console.error("Camera failed to start:", err);
});

async function handleCheckout() {
    const saleData = {
        total_price: cartTotal, // Make sure this matches your variable name
        date: new Date().toLocaleString()
    };

    const response = await fetch('http://127.0.0.1:8000/api/complete-sale', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(saleData)
    });

    if (response.ok) {
        // Trigger the PDF download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "receipt.pdf";
        document.body.appendChild(a);
        a.click();
        
        alert("Sale successful! Receipt downloaded.");
        clearCart(); // Call your function to empty the cart
    } else {
        alert("Server error during checkout.");
    }
}