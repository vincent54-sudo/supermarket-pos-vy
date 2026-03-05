const API_BASE = "https://supermarket-pos-bh4k.onrender.com/api";

export async function getInventory() {
    const response = await fetch(`${API_BASE}/inventory`);
    return await response.json();
}

export async function sellItem(itemId, quantity) {
    const response = await fetch(`${API_BASE}/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ itemId, quantity })
    });

    return await response.json();
}