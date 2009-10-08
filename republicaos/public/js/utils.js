function setInputPlaceholders() {
    $('input[type=text]').focus(
        function(){
            if($(this).val() == $(this).attr('defaultValue'))
                $(this).val('').removeClass('placeholder')
        }
    );
      
    $('input[type=text]').blur(
        function()
            {
            if($(this).val() == '')
                $(this).val($(this).attr('defaultValue')).addClass('placeholder');
            }
    );
}
