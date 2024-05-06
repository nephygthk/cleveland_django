document.addEventListener('DOMContentLoaded', function () {

    var sidebarCollapse = document.getElementById('sidebarCollapse');
    var closeSidebar = document.getElementById('closeSidebar');
    var sidebar = document.getElementById('sidebar');
    var content = document.getElementById('content');
  
    sidebarCollapse.addEventListener('click', function () {
      sidebar.classList.toggle('active');
      content.classList.toggle('active');
      toggleSidebarVisibility();
    });
  
    closeSidebar.addEventListener('click', function () {
      sidebar.classList.remove('active');
      content.classList.remove('active');
      toggleSidebarVisibility();
    });
  
    function toggleSidebarVisibility() {
      var screenWidth = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
      if (screenWidth <= 700) {
        if (sidebar.classList.contains('active')) {
          sidebar.style.display = 'block';
        } else {
          sidebar.style.display = 'none';
        }
      }
    }
  
});