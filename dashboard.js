import { getInventory } from "./api.js";
import { showToast } from "./utils.js";

// Use one name consistently (lowercase is best practice)
const spinner = document.getElementById("loadingSpinner");
const tableBody = document.querySelector("#inventoryTable tbody");

/**
 * Returns a styled HTML badge based on stock levels
 */
function getStockBadge(stock) {
    if (stock === 0) {
        return `<span class="badge badge-out">Out of Stock</span>`;
    } else if (stock < 10) {
        return `<span class="badge badge-low">Low Stock</span>`;
    } else {
        return `<span class="badge badge-ok">In Stock</span>`;
    }
}

/**
 * Fetches data from the API and updates the table
 */
async function loadInventory() {
    // Show the spinner while loading
    if (spinner) spinner.style.display = "block";

    try {
        const items = await getInventory();
        
        // Clear old table data
        tableBody.innerHTML = "";

        // Build the new table rows
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
        console.error("Load failed:", error);
        showToast("Failed to load inventory");
    } finally {
        // Hide the spinner whether it worked or failed
        if (spinner) spinner.style.display = "none";
    }
}

// Start the loading process
loadInventory();