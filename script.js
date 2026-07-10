// ==============================
// AGIChainAI Official Website
// Version: 0.1
// ==============================

console.log("🚀 AGIChainAI Website Loaded");

document.addEventListener("DOMContentLoaded", () => {

    // Sayfa yüklendiğinde animasyon
    document.body.style.opacity = "0";

    setTimeout(() => {
        document.body.style.transition = "opacity 1s ease";
        document.body.style.opacity = "1";
    }, 100);

    // Tüm butonlara tıklama efekti
    const buttons = document.querySelectorAll(".btn");

    buttons.forEach(button => {

        button.addEventListener("click", function () {

            this.style.transform = "scale(0.95)";

            setTimeout(() => {
                this.style.transform = "scale(1)";
            },150);

        });

    });

});
