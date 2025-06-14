document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    const logoutBtn = document.getElementById('logout-btn');

    // Handle login form submission
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = loginForm.elements['username'].value;
            const password = loginForm.elements['password'].value;

            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: formData.toString(),
                });

                if (response.ok) {
                    window.location.href = '/'; // Redirect to main page on success
                } else {
                    const data = await response.json(); // Assuming Flask returns JSON for errors
                    alert(data.error || 'Login failed');
                }
            } catch (error) {
                console.error('Error during login:', error);
                alert('An error occurred during login. Please try again.');
            }
        });
    }

    // Handle signup form submission
    if (signupForm) {
        signupForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = signupForm.elements['username'].value;
            const password = signupForm.elements['password'].value;
            const confirmPassword = signupForm.elements['confirm_password'].value;

            if (password !== confirmPassword) {
                alert('Passwords do not match');
                return;
            }

            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);
            formData.append('confirm_password', confirmPassword); // Include confirm_password for backend validation if needed

            try {
                const response = await fetch('/signup', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: formData.toString(),
                });

                if (response.ok) {
                    window.location.href = '/'; // Redirect to main page on success
                } else {
                    const data = await response.json(); // Assuming Flask returns JSON for errors
                    alert(data.error || 'Signup failed');
                }
            } catch (error) {
                console.error('Error during signup:', error);
                alert('An error occurred during signup. Please try again.');
            }
        });
    }

    // Handle logout button click
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function() {
            try {
                const response = await fetch('/logout', {
                    method: 'GET', // Logout is typically a GET request
                });

                if (response.ok) {
                    window.location.href = '/login'; // Redirect to login page after logout
                } else {
                    alert('Logout failed');
                }
            } catch (error) {
                console.error('Error during logout:', error);
                alert('An error occurred during logout. Please try again.');
            }
        });
    }
});
