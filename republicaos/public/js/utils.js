function setInputPlaceholders() {
    $('input[type=text][class="placeholder"]').focus(
        function(){
            if($(this).val() == $(this).attr('defaultValue'))
                $(this).val('').removeClass('_placeholder')
        }
    );
      
    $('input[type=text][class="placeholder"]').blur(
        function()
            {
            if($(this).val() == '')
                $(this).val($(this).attr('defaultValue')).addClass('_placeholder');
            }
    );
}
