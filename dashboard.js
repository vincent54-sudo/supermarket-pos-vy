
import { getInventory } from "./api.js";
import { showToast } from "./utils.js";

const Spinner = document.getElementById("loadingSpinner");
const tableBody = document.querySelector("#inventoryTable tbody");

function getStockBadge(stock) {
    if (stock === 0) {
        return `<span class="badge badge-out">Out of Stock</span>`;
    } else if (stock < 10) {
        return `<span class="badge badge-low">Low Stock</span>`;
    } else {
        return `<span class="badge badge-ok">In Stock</span>`;
    }
}

async function loadInventory() {
    spinner.style.display = "block";

    try {
        const items = await getInventory();
        tableBody.innerHTML = "";

        items.forEach(item => {
            const row = `
                <tr>
                    <td>${item.name}</td>
                    <td>${item.stock}</td>
                    <td>${getStockBadge(item.stock)}</td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });

        showToast("Inventory loaded successfully");
    } catch (error) {
        showToast("Failed to load inventory");
    }

    spinner.style.display = "none";
}

loadInventory();
function getStockBadge(stock) {
    if (stock === 0) {
        return `<span class="badge badge-out">Out of Stock</span>`;
    } else if (stock < 10) {
        return `<span class="badge badge-low">Low Stock</span>`;
    } else {
        return `<span class="badge badge-ok">In Stock</span>`;
    }
}
const spinner = document.getElementById("loadingSpinner");

async function loadInventory() {
    spinner.style.display = "block";

    const items = await getInventory();

    spinner.style.display = "none";
    
    // render table...
}