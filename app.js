// app.js

document.addEventListener("DOMContentLoaded", () => {
    const transactionsTable = document.getElementById("transactions-table").getElementsByTagName("tbody")[0];
    const monthSelect = document.getElementById("month-select");
    const searchInput = document.getElementById("search");
    const prevPageBtn = document.getElementById("prev-page");
    const nextPageBtn = document.getElementById("next-page");
    const pageNumberElement = document.getElementById("page-number");

    let currentPage = 1;
    let searchQuery = '';
    let currentMonth = monthSelect.value;

    // Fetch transactions from API
    async function fetchTransactions(month, page = 1, search = '') {
        const response = await fetch(`/api/transactions?month=${month}&page=${page}&search=${search}`);
        const data = await response.json();
        return data;
    }

    // Render transactions in the table
    function renderTransactions(transactions) {
        transactionsTable.innerHTML = ''; // Clear the table first
        transactions.forEach(transaction => {
            const row = transactionsTable.insertRow();
            row.innerHTML = `
                <td>${transaction.id}</td>
                <td>${transaction.title}</td>
                <td>${transaction.description}</td>
                <td>${transaction.price}</td>
                <td>${transaction.category}</td>
                <td>${transaction.sold ? "Yes" : "No"}</td>
                <td><img src="${transaction.image}" alt="Image" width="50"></td>
            `;
        });
    }

    // Load initial transactions
    async function loadTransactions() {
        const data = await fetchTransactions(currentMonth, currentPage, searchQuery);
        renderTransactions(data.transactions);
        updatePagination(data.totalPages);
    }

    // Handle pagination updates
    function updatePagination(totalPages) {
        prevPageBtn.disabled = currentPage === 1;
        nextPageBtn.disabled = currentPage === totalPages;
        pageNumberElement.textContent = `Page No: ${currentPage}`;
    }

    // Event Listeners
    monthSelect.addEventListener("change", async () => {
        currentMonth = monthSelect.value;
        currentPage = 1; // Reset to the first page
        await loadTransactions();
    });

    searchInput.addEventListener("input", async () => {
        searchQuery = searchInput.value;
        currentPage = 1; // Reset to the first page
        await loadTransactions();
    });

    prevPageBtn.addEventListener("click", async () => {
        if (currentPage > 1) {
            currentPage--;
            await loadTransactions();
        }
    });

    nextPageBtn.addEventListener("click", async () => {
        currentPage++;
        await loadTransactions();
    });

    // Initial load for March
    loadTransactions();
});
