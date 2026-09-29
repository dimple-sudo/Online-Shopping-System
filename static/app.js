/**
 * Online Shopping System - Vanilla JavaScript Client
 * Interacts with Flask JSON APIs via fetch() and updates the UI dynamically.
 */

// Helper to display clean inline notification banner without alert()
function showMessage(elementId, text, isSuccess) {
  const container = document.getElementById(elementId);
  if (!container) return;

  container.className = isSuccess ? 'message-box message-success' : 'message-box message-error';
  container.textContent = text;
  container.style.display = 'block';

  // Scroll into view if needed
  container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function clearMessage(elementId) {
  const container = document.getElementById(elementId);
  if (container) {
    container.style.display = 'none';
    container.textContent = '';
  }
}

// Update the cart badge count in the top navbar
function updateCartBadge(count) {
  const badge = document.getElementById('navbar-cart-count');
  if (badge) {
    badge.textContent = count;
  }
}

// ----------------------------------------------------
// Authentication Handlers
// ----------------------------------------------------

async function handleRegister(event) {
  event.preventDefault();
  clearMessage('register-message');

  const name = document.getElementById('reg-name').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const submitBtn = document.getElementById('reg-submit-btn');

  if (!name || !email || !password) {
    showMessage('register-message', 'All fields are required.', false);
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Registering...';

  try {
    const res = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
    });
    const result = await res.json();

    if (result.ok) {
      showMessage('register-message', 'Registration successful! Redirecting to login...', true);
      setTimeout(() => {
        window.location.href = '/login';
      }, 1200);
    } else {
      showMessage('register-message', result.error || 'Registration failed.', false);
      submitBtn.disabled = false;
      submitBtn.textContent = 'Register';
    }
  } catch (err) {
    showMessage('register-message', 'Network error. Please try again.', false);
    submitBtn.disabled = false;
    submitBtn.textContent = 'Register';
  }
}

async function handleLogin(event) {
  event.preventDefault();
  clearMessage('login-message');

  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  const asAdmin = document.getElementById('login-as-admin') ? document.getElementById('login-as-admin').checked : false;
  const submitBtn = document.getElementById('login-submit-btn');

  if (!email || !password) {
    showMessage('login-message', 'Please enter both email and password.', false);
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Logging in...';

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, as_admin: asAdmin }),
    });
    const result = await res.json();

    if (result.ok) {
      showMessage('login-message', 'Login successful! Redirecting...', true);
      setTimeout(() => {
        if (result.data.user.role === 'admin') {
          window.location.href = '/admin';
        } else {
          window.location.href = '/products';
        }
      }, 800);
    } else {
      showMessage('login-message', result.error || 'Authentication failed.', false);
      submitBtn.disabled = false;
      submitBtn.textContent = 'Login';
    }
  } catch (err) {
    showMessage('login-message', 'Network error. Please try again.', false);
    submitBtn.disabled = false;
    submitBtn.textContent = 'Login';
  }
}

// ----------------------------------------------------
// Product & Cart Operations
// ----------------------------------------------------

async function addToCart(productId) {
  clearMessage('products-message');
  const qtyInput = document.getElementById(`qty-${productId}`);
  const quantity = qtyInput ? parseInt(qtyInput.value, 10) : 1;

  if (isNaN(quantity) || quantity <= 0) {
    showMessage('products-message', 'Please enter a valid quantity greater than 0.', false);
    return;
  }

  try {
    const res = await fetch('/api/cart/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId, quantity: quantity }),
    });
    const result = await res.json();

    if (result.ok) {
      showMessage('products-message', result.data.message, true);
      updateCartBadge(result.data.cart_count);
    } else {
      showMessage('products-message', result.error || 'Could not add to cart.', false);
    }
  } catch (err) {
    showMessage('products-message', 'Network error adding item to cart.', false);
  }
}

async function removeFromCart(productId) {
  clearMessage('cart-message');

  try {
    const res = await fetch('/api/cart/remove', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId }),
    });
    const result = await res.json();

    if (result.ok) {
      showMessage('cart-message', 'Item removed from cart.', true);
      updateCartBadge(result.data.cart_count);
      // Reload cart view to refresh table and calculations
      setTimeout(() => {
        window.location.reload();
      }, 500);
    } else {
      showMessage('cart-message', result.error || 'Failed to remove item.', false);
    }
  } catch (err) {
    showMessage('cart-message', 'Network error removing item.', false);
  }
}

// ----------------------------------------------------
// Checkout Operations
// ----------------------------------------------------

async function handleCheckout(event) {
  event.preventDefault();
  clearMessage('checkout-message');

  const methodRadios = document.getElementsByName('payment_method');
  let selectedMethod = 'UPI';
  for (const radio of methodRadios) {
    if (radio.checked) {
      selectedMethod = radio.value;
      break;
    }
  }

  const simulateFailCheckbox = document.getElementById('simulate-fail');
  const simulateFail = simulateFailCheckbox ? simulateFailCheckbox.checked : false;
  const payBtn = document.getElementById('pay-button');

  payBtn.disabled = true;
  payBtn.textContent = 'Processing Payment...';

  try {
    const res = await fetch('/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        method: selectedMethod,
        simulate_fail: simulateFail,
      }),
    });
    const result = await res.json();

    if (result.ok) {
      const order = result.data;
      updateCartBadge(0);
      const successHtml = `Order placed successfully! Order #${order.order_id} recorded. Total paid: ₹${order.totals.total.toFixed(2)} via ${order.payment_method}.`;
      showMessage('checkout-message', successHtml, true);

      // Hide checkout form and provide button to orders
      const form = document.getElementById('checkout-form');
      if (form) form.style.display = 'none';

      const successBox = document.getElementById('checkout-success-view');
      if (successBox) {
        successBox.style.display = 'block';
        const details = document.getElementById('order-summary-details');
        if (details) {
          details.innerHTML = `
            <p><strong>Order ID:</strong> #${order.order_id}</p>
            <p><strong>Date:</strong> ${order.order_date}</p>
            <p><strong>Payment Method:</strong> ${order.payment_method}</p>
            <p><strong>Payment Status:</strong> ${order.payment_status}</p>
            <p><strong>Total Paid:</strong> ₹${order.totals.total.toFixed(2)}</p>
          `;
        }
      }
    } else {
      showMessage('checkout-message', result.error || 'Payment failed.', false);
      payBtn.disabled = false;
      payBtn.textContent = 'Confirm & Pay';
    }
  } catch (err) {
    showMessage('checkout-message', 'Network error during payment processing.', false);
    payBtn.disabled = false;
    payBtn.textContent = 'Confirm & Pay';
  }
}

// ----------------------------------------------------
// Admin Operations
// ----------------------------------------------------

async function handleAdminAddProduct(event) {
  event.preventDefault();
  clearMessage('admin-message');

  const name = document.getElementById('admin-prod-name').value.trim();
  const category = document.getElementById('admin-prod-category').value.trim();
  const price = document.getElementById('admin-prod-price').value;
  const stock = document.getElementById('admin-prod-stock').value;
  const btn = document.getElementById('admin-add-btn');

  btn.disabled = true;
  btn.textContent = 'Adding Product...';

  try {
    const res = await fetch('/api/admin/product', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, category, price, stock }),
    });
    const result = await res.json();

    if (result.ok) {
      showMessage('admin-message', result.data.message, true);
      document.getElementById('admin-prod-name').value = '';
      document.getElementById('admin-prod-price').value = '';
      document.getElementById('admin-prod-stock').value = '';
      setTimeout(() => {
        window.location.reload();
      }, 900);
    } else {
      showMessage('admin-message', result.error || 'Failed to add product.', false);
      btn.disabled = false;
      btn.textContent = 'Add Product';
    }
  } catch (err) {
    showMessage('admin-message', 'Network error while adding product.', false);
    btn.disabled = false;
    btn.textContent = 'Add Product';
  }
}

async function handleAdminUpdateStock(event) {
  event.preventDefault();
  clearMessage('admin-message');

  const productId = document.getElementById('admin-stock-id').value;
  const newStock = document.getElementById('admin-stock-qty').value;
  const btn = document.getElementById('admin-stock-btn');

  btn.disabled = true;
  btn.textContent = 'Updating...';

  try {
    const res = await fetch('/api/admin/stock', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId, new_stock: newStock }),
    });
    const result = await res.json();

    if (result.ok) {
      showMessage('admin-message', result.data.message, true);
      document.getElementById('admin-stock-qty').value = '';
      setTimeout(() => {
        window.location.reload();
      }, 900);
    } else {
      showMessage('admin-message', result.error || 'Failed to update stock.', false);
      btn.disabled = false;
      btn.textContent = 'Update Stock';
    }
  } catch (err) {
    showMessage('admin-message', 'Network error while updating stock.', false);
    btn.disabled = false;
    btn.textContent = 'Update Stock';
  }
}
