// settings.js
$(document).ready(function() {
    // Show the settings modal when the settings button is clicked
    $('#settingsDropdown').on('click', function() {
      $('#settingsModal').modal('show');
    });
  
    // Apply saved settings on page load
    applySettings(loadSettings());
  
    // Add event listeners for setting changes
    $('.custom-control-input').on('change', function() {
      const settings = getSettingsFromForm();
      applySettings(settings);
      saveSettings(settings);
    });
  
    // Load settings from local storage
    function loadSettings() {
      const settings = localStorage.getItem('adminSettings');
      return settings ? JSON.parse(settings) : getDefaultSettings();
    }
  
    // Save settings to local storage
    function saveSettings(settings) {
      localStorage.setItem('adminSettings', JSON.stringify(settings));
    }
  
    // Get default settings
    function getDefaultSettings() {
      return {
        darkMode: false,
        headerFixed: false,
        dropdownLegacyOffset: false,
        noBorder: false,
        sidebarCollapsed: false,
        sidebarFixed: false,
        sidebarMini: false,
        sidebarMiniMD: false,
        sidebarMiniXS: false,
        navFlatStyle: false,
        navLegacyStyle: false,
        navCompact: false,
        navChildIndent: false,
        navChildHideOnCollapse: false,
        disableHoverFocusAutoExpand: false,
        footerFixed: false,
        smallTextBody: false,
        smallTextNavbar: false,
        smallTextBrand: false,
        smallTextSidebarNav: false
      };
    }
  
    // Get settings from the form inputs
    function getSettingsFromForm() {
      return {
        darkMode: $('#darkMode').is(':checked'),
        headerFixed: $('#headerFixed').is(':checked'),
        dropdownLegacyOffset: $('#dropdownLegacyOffset').is(':checked'),
        noBorder: $('#noBorder').is(':checked'),
        sidebarCollapsed: $('#sidebarCollapsed').is(':checked'),
        sidebarFixed: $('#sidebarFixed').is(':checked'),
        sidebarMini: $('#sidebarMini').is(':checked'),
        sidebarMiniMD: $('#sidebarMiniMD').is(':checked'),
        sidebarMiniXS: $('#sidebarMiniXS').is(':checked'),
        navFlatStyle: $('#navFlatStyle').is(':checked'),
        navLegacyStyle: $('#navLegacyStyle').is(':checked'),
        navCompact: $('#navCompact').is(':checked'),
        navChildIndent: $('#navChildIndent').is(':checked'),
        navChildHideOnCollapse: $('#navChildHideOnCollapse').is(':checked'),
        disableHoverFocusAutoExpand: $('#disableHoverFocusAutoExpand').is(':checked'),
        footerFixed: $('#footerFixed').is(':checked'),
        smallTextBody: $('#smallTextBody').is(':checked'),
        smallTextNavbar: $('#smallTextNavbar').is(':checked'),
        smallTextBrand: $('#smallTextBrand').is(':checked'),
        smallTextSidebarNav: $('#smallTextSidebarNav').is(':checked')
      };
    }
  
    // Apply settings to the page
    function applySettings(settings) {
      $('body').toggleClass('dark-mode', settings.darkMode);
      $('.navbar').toggleClass('fixed-top', settings.headerFixed);
      $('.navbar').toggleClass('no-border', settings.noBorder);
      $('.sidebar').toggleClass('sidebar-collapse', settings.sidebarCollapsed);
      $('.sidebar').toggleClass('sidebar-fixed', settings.sidebarFixed);
      $('.sidebar').toggleClass('sidebar-mini', settings.sidebarMini);
      $('.sidebar').toggleClass('sidebar-mini-md', settings.sidebarMiniMD);
      $('.sidebar').toggleClass('sidebar-mini-xs', settings.sidebarMiniXS);
      $('.nav').toggleClass('nav-flat', settings.navFlatStyle);
      $('.nav').toggleClass('nav-legacy', settings.navLegacyStyle);
      $('.nav').toggleClass('nav-compact', settings.navCompact);
      $('.nav').toggleClass('nav-child-indent', settings.navChildIndent);
      $('.nav').toggleClass('nav-collapse-hide-child', settings.navChildHideOnCollapse);
      $('.nav').toggleClass('nav-no-expand', settings.disableHoverFocusAutoExpand);
      $('.footer').toggleClass('footer-fixed', settings.footerFixed);
      $('body').toggleClass('text-sm', settings.smallTextBody);
      $('.navbar').toggleClass('text-sm', settings.smallTextNavbar);
      $('.brand-link').toggleClass('text-sm', settings.smallTextBrand);
      $('.nav-sidebar').toggleClass('text-sm', settings.smallTextSidebarNav);
    }
  });
  