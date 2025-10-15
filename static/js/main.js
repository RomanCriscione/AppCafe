// static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
  // Helper CSRF para fetch POST
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
  }
  window.csrftoken = getCookie('csrftoken') || '';


});
