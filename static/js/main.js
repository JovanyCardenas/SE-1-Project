if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker
            .register("/static/serviceworker.js")
            .catch(error => {
                console.log("Service worker registration failed:", error);
            });
    });
}
