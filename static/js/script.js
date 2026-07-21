document.addEventListener('DOMContentLoaded', () => {
    // Password Visibility Toggle
    const togglePassword = document.querySelectorAll('.toggle-password');
    togglePassword.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const inputId = this.getAttribute('data-target');
            const input = document.getElementById(inputId);
            
            if (input.type === 'password') {
                input.type = 'text';
                this.classList.remove('fa-eye');
                this.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                this.classList.remove('fa-eye-slash');
                this.classList.add('fa-eye');
            }
        });
    });

    // Auto-dismiss Flash Messages
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(flash => {
        // Only dismiss success or info messages automatically
        if (flash.classList.contains('success')) {
            setTimeout(() => {
                flash.style.opacity = '0';
                flash.style.transform = 'translateY(-10px)';
                flash.style.transition = 'all 0.3s ease';
                setTimeout(() => flash.remove(), 300);
            }, 4000);
        }
    });
});
