document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('import-form');

    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault(); // Stop default form submission

            const formData = new FormData(form);

            fetch('/datasetimporter/form', {
                method: 'POST',
                body: formData
            })
            .then(response => response.text())
            .then(text => {
                const urlParams = new URLSearchParams(text);
                const taskId = urlParams.get("task");

                if (taskId) {
                    const link = `/datasetimporter/status?task=${taskId}`;

                    document.getElementById('progress-link').style.display = 'block';
                    document.getElementById('link-text').innerText = window.location.origin + link;

                    const box = document.getElementById('status-box');
                    box.style.display = 'block';
                    box.innerHTML = "⏳ Upload submitted. Monitoring...";

                    const interval = setInterval(() => {
                        fetch(link)
                            .then(res => res.text())
                            .then(statusText => {
                                box.innerHTML = statusText;
                                if (statusText.includes("✅ Done") || statusText.includes("❌ Error")) {
                                    box.className = statusText.includes("✅ Done") ? "alert alert-success" : "alert alert-danger";
                                    clearInterval(interval);
                                }
                            });
                    }, 2000);
                }
            })
            .catch(err => {
                alert("Something went wrong! " + err);
            });
        });
    }
});

function copyLink() {
    const text = document.getElementById('link-text').innerText;
    navigator.clipboard.writeText(text).then(function () {
        alert('Link copied to clipboard!');
    });
}
