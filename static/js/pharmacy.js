// Cart functionality
let cart = JSON.parse(localStorage.getItem("cart")) || [];
const deliveryFee = 150;

// DOM Elements
const cartButton = document.getElementById("cart-button");
const cartSidebar = document.getElementById("cart-sidebar");
const closeCartButton = document.getElementById("close-cart");
const cartItemsElement = document.getElementById("cart-items");
const emptyCartElement = document.getElementById("empty-cart-message");
const cartCountElement = document.getElementById("cart-count");
const checkoutButton = document.getElementById("checkout-button");
const paymentModal = document.getElementById("payment-modal");
const closePaymentModalButton = document.getElementById("close-payment-modal");
const cancelPaymentButton = document.getElementById("cancel-payment");
const confirmPaymentButton = document.getElementById("confirm-payment");
const paymentProcessingModal = document.getElementById("payment-processing");
const paymentSuccessModal = document.getElementById("payment-success");
const continueShoppingButton = document.getElementById("continue-shopping");
const searchInput = document.getElementById("search-input");
const productsGrid = document.getElementById("products-grid");
const itemsCountElement = document.getElementById("items-count");

// Original products data (for search functionality)
const originalProducts = Array.from(document.querySelectorAll('.item-card')).map(card => ({
    element: card,
    name: card.querySelector('h3').textContent.toLowerCase(),
    description: card.querySelector('p').textContent.toLowerCase()
}));

// Initialize cart
updateCartCount();

// Event Listeners
cartButton.addEventListener("click", showCart);
closeCartButton.addEventListener("click", closeCart);
checkoutButton.addEventListener("click", checkout);
closePaymentModalButton.addEventListener("click", closePaymentModal);
cancelPaymentButton.addEventListener("click", closePaymentModal);
confirmPaymentButton.addEventListener("click", payWithMpesa);
continueShoppingButton.addEventListener("click", closeSuccessModal);
searchInput.addEventListener("input", handleSearch);

// Close cart when clicking outside
cartSidebar.addEventListener("click", function(e) {
    if (e.target === cartSidebar) {
        closeCart();
    }
});

// Functions
function showCart() {
    cartSidebar.classList.remove("translate-x-full");
    document.body.classList.add("overflow-hidden");
    updateCart();
}

function closeCart() {
    cartSidebar.classList.add("translate-x-full");
    document.body.classList.remove("overflow-hidden");
}

function addToCart(id, name, price) {
    cart.push({ id, name, price });
    localStorage.setItem("cart", JSON.stringify(cart));
    updateCartCount();
    
    // Show added notification
    showNotification(`${name} added to cart`, "bg-green-500", "fa-check-circle");
    updateCart();
}

function updateCart() {
    cartItemsElement.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        emptyCartElement.classList.remove("hidden");
    } else {
        emptyCartElement.classList.add("hidden");
        cart.forEach((item, index) => {
            cartItemsElement.innerHTML += `
                <li class="flex justify-between items-center p-3 bg-white rounded-lg border border-gray-100">
                    <div class="flex-1">
                        <p class="font-medium text-gray-800">${item.name}</p>
                        <p class="text-sm text-gray-500">KES ${item.price.toLocaleString()}</p>
                    </div>
                    <button onclick="removeItem(${index})" class="text-red-500 hover:text-red-700 p-2 rounded-full hover:bg-red-50">
                        <i class="fas fa-trash"></i>
                    </button>
                </li>
            `;
            total += item.price;
        });
    }

    document.getElementById("total-price").textContent = total.toLocaleString();
    document.getElementById("checkout-total").textContent = (total + deliveryFee).toLocaleString();
}

function updateCartCount() {
    if (cart.length > 0) {
        cartCountElement.textContent = cart.length;
        cartCountElement.classList.remove("hidden");
    } else {
        cartCountElement.classList.add("hidden");
    }
}

function removeItem(index) {
    const removedItem = cart[index];
    cart.splice(index, 1);
    localStorage.setItem("cart", JSON.stringify(cart));
    updateCart();
    updateCartCount();
    
    // Show removed notification
    showNotification(`${removedItem.name} removed from cart`, "bg-red-500", "fa-trash-alt");
}

function checkout() {
    if (cart.length === 0) {
        showNotification("Your cart is empty!", "bg-red-500", "fa-exclamation-circle");
        return;
    }
    showPaymentModal();
}

function showPaymentModal() {
    paymentModal.classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
}

function closePaymentModal() {
    paymentModal.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
}

function showProcessingModal() {
    paymentProcessingModal.classList.remove("hidden");
}

function closeProcessingModal() {
    paymentProcessingModal.classList.add("hidden");
}

function showSuccessModal() {
    paymentSuccessModal.classList.remove("hidden");
}

function closeSuccessModal() {
    paymentSuccessModal.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
    closeCart();
}

function payWithMpesa() {
    const phoneNumber = document.getElementById("phone-number").value;
    if (!phoneNumber || !phoneNumber.match(/^07[0-9]{8}$/)) {
        showNotification("Please enter a valid M-Pesa number (07XXXXXXXX)", "bg-red-500", "fa-exclamation-circle");
        return;
    }
    
    closePaymentModal();
    showProcessingModal();
    
    // Simulate payment processing
    setTimeout(() => {
        closeProcessingModal();
        showSuccessModal();
        
        // Clear cart after successful payment
        cart = [];
        localStorage.setItem("cart", JSON.stringify(cart));
        updateCart();
        updateCartCount();
    }, 3000);
}

function handleSearch() {
    const searchTerm = searchInput.value.toLowerCase();
    
    if (searchTerm === '') {
        // Show all products if search is empty
        originalProducts.forEach(product => {
            product.element.classList.remove("hidden");
        });
        itemsCountElement.textContent = `${originalProducts.length} items`;
        return;
    }
    
    let visibleCount = 0;
    
    originalProducts.forEach(product => {
        const matches = product.name.includes(searchTerm) || product.description.includes(searchTerm);
        if (matches) {
            product.element.classList.remove("hidden");
            visibleCount++;
        } else {
            product.element.classList.add("hidden");
        }
    });
    
    itemsCountElement.textContent = `${visibleCount} ${visibleCount === 1 ? 'item' : 'items'}`;
}

function showNotification(message, bgColor, icon) {
    const notification = document.createElement("div");
    notification.className = `fixed bottom-6 left-6 ${bgColor} text-white px-4 py-3 rounded-lg shadow-xl flex items-center fade-in z-50`;
    notification.innerHTML = `
        <i class="fas ${icon} mr-2"></i>
        ${message}
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add("opacity-0", "transition-opacity", "duration-300");
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

// Make functions available globally
window.addToCart = addToCart;
window.removeItem = removeItem;