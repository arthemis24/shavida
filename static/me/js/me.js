/*!
 * Name:        mycvb
 * Version:     1.0
 * Description:
 * Author:      Kom Sihon
 * Support:     http://d-krypt.com
 *
 * Depends:
 *      jquery.js http://jquery.org
 *
 * Date: Thu Sep 04 15:22:55 2014 -0500
 */
(function(c) {
    c.listOrders = function(endPoint, origin, fn, start, limit) {
    	if (!start) start = 0;
    	if (!limit) limit = 1000000;
    	var params = {origin: origin, start: start, limit: limit};
        $.getJSON(endPoint, params, function(data) {
            if (data.error)
                $('#submit-result').text(data.error);
            else {
                $('div#content .spinner').hide();
                if (data.length > 0) {
                    c.orders = data;
                    populateOrderPanel(c.orders, fn)
                } else {
                    $('div#content .no-result').show()
                }
            }
        })
    };

    function populateOrderPanel(objects, fn) {
        $('div#content .spinner').hide();
        $('.items-row.empty-resultset').remove();
        $('.master .order').not('.tpl').remove();
        if (objects.length == 0) {
            var $emptyResult = $('<div class="items-row empty-resultset">Aucune Commande trouvée</div>');
            $emptyResult.insertBefore('.items-row:first');
            return
        }
        var $list = $('<div></div>');
        for (var i = 0; i < objects.length; i++) {
            if (i % 4 == 0) {
                var $fiveOrdersRow = $('<div class="order-row"></div>')
            }
            var $newRow = $('.row .master').find('.order.tpl').clone().removeClass('tpl');
            $newRow = applyOrderHistoryTemplate($newRow, objects[i]).show();
            $fiveOrdersRow.append($newRow);
            if ($fiveOrdersRow.children().length == 4 || i == (objects.length - 1))
                $list.append($fiveOrdersRow)
        }
        $list.children().insertBefore('.master .order.tpl');
        if (fn) fn()
    }

    function applyOrderHistoryTemplate($tpl, order) {
        $tpl.attr({id: order.id, status: order.status});
        //if (order.movies) $tpl.find('img').attr('src',   order.movies[0].poster_small )
        if (order.movies) $tpl.find('.poster').css('background-image', "url('" + order.movies[0].poster_small +"')");
        $tpl.find('.date').text(order.when);
        $tpl.find('.summary .size').text(order.movies.length);
        $tpl.find('.summary .amount').text(order.cost);
        for (var i = 0; i < order.movies.length; i++) {
            var $itemTpl = $('.details .movie.tpl').clone().removeClass('tpl');
            var $movieTpl = applyHistoryDetailMovieTemplate($itemTpl, order.movies[i], order.id);
            $movieTpl.insertBefore('.details .movie.tpl')
        }
        return $tpl
    }

    function applyHistoryDetailMovieTemplate($tpl, movie, orderId) {
        $tpl.attr('orderId', orderId);
        $tpl.attr('movieId', movie.id);
        $tpl.attr('cost', movie.price);
        $tpl.attr('size', movie.size);
        $tpl.attr('type', movie.type);
        $tpl.attr('title', movie.title);
        $tpl.find('.title').text(movie.title);
        $tpl.find('.cost .value').text(movie.price);
        $tpl.css('background-image', "url('" + movie.poster_small +"')");
        return $tpl
    }

    c.cancelOrder = function(endpoint, orderId) {
    	var params = {order_id: orderId};
        $.getJSON(endpoint, params, function(data) {
            if (data.error)
                console.log(data.error);
            else {
                $('#' + orderId).fadeOut('normal', function() {
                    $(this).remove()
                });
                $('.details .movie[orderId=' + orderId + ']').remove();
                $('.details').hide();
                window.location = '/'
            }
        })
    }

})(ikwen);

