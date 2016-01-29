/*!
 * Name:        movies
 * Version:     1.2
 * Description: 
 * Author:      Kom Sihon & Mbogning Rodrigue
 * Support:     http://www.ikwen.com
 *
 * Depends:
 *      jquery.js http://jquery.org
 *
 * Date: Mon Jan 29 02:04:55 2014 -0500
 */

(function(c) {
    ikwen.DEFAULT_LIMIT_PER_PAGE = 12;
    var FIVE_PAGE_LIMIT = ikwen.DEFAULT_LIMIT_PER_PAGE * 5;
    var ajaxLoading = false;
    var MAX_VISIBLE_CART_ITEMS = 24;
    c.dataSourceIsEmpty = false;
    c.nextStartIndex = 0;
    c.media = [];
    var startMovies = 0, startSeries = 0;
    ikwen.initialSelectedItems =[];
    c.listItems = function(endPoint, categoryId, startMovies, startSeries) {
        if (c.dataSourceIsEmpty) return;
        ajaxLoading = true;
        endPoint = ikwen.mediaEndpoint;
        if (!startMovies) startMovies = 0;
        if (!startSeries) startSeries = 0;
        $('#content').find('.spinner').show();
        var params = {format: 'json', category_id: categoryId, start_movies: startMovies, start_series: startSeries, length: FIVE_PAGE_LIMIT};
        $.getJSON(endPoint, params, function(data) {
            if (data.error)
                $('#submit-result').text(data.error);
            else {
                $('#content').find('.spinner').hide();
                for (var i=0; i<data.length; i++)
                    c.media.push(data[i])
                if (c.media.length == 0) {
                    var $emptyResult = $('<div class="no-result" colspan="10"> Aucune donnée trouvée </div>');
                    $emptyResult.insertBefore('#content td.tpl')
                }
                if (data.length == 0) {
                    c.dataSourceIsEmpty = true;
                    return
                }
                if (categoryId == ikwen.currentCategoryId && c.media.length > 0) c.showNextPage();
                ajaxLoading = false;
            }
        })
    };

    c.listItemsForHome = function(endPoint, category, templateFunction) {
        var $newSection = $('div#content section.tpl').clone().removeClass('tpl'),
            params = {format: 'json', category_id: category.id, start_movies: 0, start_series: 0},
            movies = [];
        if (category.slug != 'top') {
            if (category.previewsTitle != 'None' && category.previewsTitle != '' )
                $newSection.insertBefore('section.tpl').addClass(category.slug).show().find('header span').text(category.previewsTitle);
            else
                $newSection.insertBefore('section.tpl').addClass(category.slug).show().find('header span').text(category.title);
            templateFunction($newSection, category)
        }
        $.getJSON(endPoint, params, function(data) {
            if (data.error)
                $('#submit-result').text(data.error);
            else {
                $newSection.find('.spinner').hide();
                if (data.length == 0) {
                    $newSection.remove();
                    return;
                }
                movies = data;
                var $targetSection = $('div#content section.' + category.slug);
                populateHomeMoviePanel(movies, $targetSection);
            }
        })
    };

    function populateHomeMoviePanel(objects, $newSection) {
        var $list = $('<div></div>');
        for (var i = 0; i < objects.length; i++) {
            if (i % 4 == 0) {
                var $fourItemsRow = $('<tr class="item-row"></tr>')
            }
            var $newRow = ($newSection).find('table.items td.tpl').clone().removeClass('tpl');
            $newRow = applyHomeItemTemplate($newRow, objects[i]).show();
            $fourItemsRow.append($newRow);
            if ($fourItemsRow.children().length == 4)
                $list.append($fourItemsRow)
        }
        $newSection.find('table td.tpl').before($list.children())
        updateButtonsState()
    }
    function populateHomeTopPanel(objects, selector, is_main) {
        for (var i = 0; i < objects.length; i++) {
            var parentSelector = 'div.four-img';
            var $newRow = $(parentSelector + '.' + selector).find('div.item.tpl').clone().removeClass('tpl');
            if (is_main) $newRow = applyHomeItemTemplate($newRow, objects[i], true).show();
            else $newRow = applyHomeItemTemplate($newRow, objects[i], false).show();
            $newRow.insertBefore(parentSelector + '.' + selector +' div.item.tpl')
        }
        updateButtonsState()
    }
    

    c.selectedItems = [];
    c.showNextPage = function() {
        if (c.nextStartIndex >= c.media.length) {
            if (ajaxLoading) return;
            c.listItems(ikwen.mediaEndpoint, ikwen.currentCategoryId, startMovies, startSeries);
            c.nextStartIndex = Math.min(c.nextStartIndex, c.media.length);
            return
        }
        var start = c.nextStartIndex;
        var end = Math.min(start + ikwen.DEFAULT_LIMIT_PER_PAGE, c.media.length);
        var pageItems = [];
        for (var i=start; i<end; i++) {
            pageItems.push(c.media[i]);
            if (c.media[i].type == 'movie') startMovies += 1;
            else startSeries += 1;
        }
        populateMoviePanel(pageItems);
        c.nextStartIndex = end
    };

    function populateMoviePanel(objects) {
        var $list = $('<div></div>');
        if (objects.length == 0) {
            var $emptyResult = $('<div class="no-result">Aucune donnée trouvée</div>');
            $emptyResult.insertBefore('#content .spinner');
            return
        }
        for (var i = 0; i < objects.length; i++) {
            if (i % 4 == 0) {
                var $fourItemsRow = $('<tr class="item-row"></tr>')
            }
            var $newRow = $('section').find('table td.tpl').clone().removeClass('tpl');
            $newRow = applyHomeItemTemplate($newRow, objects[i]).show();
            $fourItemsRow.append($newRow);
            //if ($fourItemsRow.children().length == 4)
                $list.append($fourItemsRow)
        }
        $list.children().insertBefore('#content section table td.tpl');
        updateButtonsState()
    }

    c.submitOrderInfo = function(endpoint, items, fn) {
    	$('body, #summary .button.default').css('cursor', 'wait');
        $.getJSON(endpoint, {items: items}, function(order) {
            $('body, .button').css('cursor', 'default');
            if (order.error) {
                $('.top-notice-ctnr span').addClass('failure').html(order.error);
                $('.top-notice-ctnr').hide().fadeIn('slow')
            } else {
                $('div#top .items-count span').text('0');
                localStorage.removeItem('movieSelection');
                localStorage.removeItem('seriesSelection');
                localStorage.removeItem('itemsCount');
                localStorage.removeItem('downloadSpeed');
                $('div#summary .button.confirm').removeClass('confirm').addClass('disabled');
                if (fn) fn(order)
            }
        })
    };

    c.populateCartPanel = function() {
        $("div#cart .item:not(.tpl)").remove();
        var itemsCount = localStorage.getItem('itemsCount') ? localStorage.getItem('itemsCount') : 0;
        var movieSelection = localStorage.getItem('movieSelection') ? JSON.parse(localStorage.getItem('movieSelection')) : [];
        var seriesSelection = localStorage.getItem('seriesSelection') ? JSON.parse(localStorage.getItem('seriesSelection')) : [];
        var moviesLength = Math.min(movieSelection.length, MAX_VISIBLE_CART_ITEMS),
            seriesLength = Math.min(seriesSelection.length, MAX_VISIBLE_CART_ITEMS);
        for (var i=0; i<moviesLength; i++) {
            var $itemTpl = $('div#cart .item.tpl').clone().removeClass('tpl');
            $itemTpl = applyCartContentTemplate($itemTpl, movieSelection[i]);
            $itemTpl.insertBefore('#cart .item.tpl')
        }
        for (var j=0; j<seriesLength; j++) {
            var $itemTpl = $('div#cart .item.tpl').clone().removeClass('tpl');
            $itemTpl = applyCartContentTemplate($itemTpl, seriesSelection[j]);
            $itemTpl.insertBefore('#cart .item.tpl').show()
        }
        if (ikwen.limitCartItems) {
            if (itemsCount > MAX_VISIBLE_CART_ITEMS) {
                var more = parseInt(itemsCount) - MAX_VISIBLE_CART_ITEMS;
                $('div#cart .more').show().find('em').text(more);
            } else
                $('div#cart .more').hide();
        }
        var amount = 0;
        $('div#cart .item').not('.tpl').each(function() {
            var cost = $(this).find('.about .cost span.value').text();
            amount = parseInt(amount) + parseInt(cost)
        });
        $('.actions .cost .value ').text(amount);
        $('div#cart .items-count span').text(itemsCount);
        if ($('div#cart .item:not(.tpl)').length == 0) $('div#cart .no-movie').show();
        else $('div#cart .no-movie').hide();
        loadGauge();
        updateButtonsState()
    };

    function loadGauge() {
        var usedQuota = ikwen.getUsedQuota(),
            maxGaugeWidth = $('div#cart .quota').width(),
            ratio = 0;
        if (ikwen.availableQuota) ratio = usedQuota / ikwen.availableQuota;
        $('.controls .quota .text-view .used').text(Math.round((ratio * 100) * 100) / 100);
        var usedWidth = ratio * maxGaugeWidth;
        if (ratio > 3/4) {
            $('.controls .quota .gauge').removeClass('normal').addClass('critical')
        } else {
            $('.controls .quota .gauge').removeClass('critical').addClass('normal');
        }
        $('.controls .storage .gauge .fill').animate({width: usedWidth + 'px'}, 'slow', 'swing');
    }

    c.addToCart = function(item, index) {
        var itemsCount = localStorage.getItem('itemsCount'),
            movieSelection = localStorage.getItem('movieSelection'),
            seriesSelection = localStorage.getItem('seriesSelection');
        if (itemsCount) itemsCount = parseInt(itemsCount) + 1;
        else itemsCount = 1;
        if (movieSelection) movieSelection = JSON.parse(movieSelection);
        else movieSelection = [];
        if (seriesSelection) seriesSelection = JSON.parse(seriesSelection);
        else seriesSelection = [];
        if (index !== null) {
            if (item.type == 'movie') movieSelection.splice(index, 0, item);
            else seriesSelection.splice(index, 0, item)
        } else {
            if (item.type == 'movie') movieSelection.push(item);
            else seriesSelection.push(item)
        }
        localStorage.setItem('itemsCount', itemsCount);
        localStorage.setItem('movieSelection', JSON.stringify(movieSelection));
        localStorage.setItem('seriesSelection', JSON.stringify(seriesSelection))
    };

    function updateButtonsState() {
        var movieSelection = localStorage.getItem('movieSelection'),
            seriesSelection = localStorage.getItem('seriesSelection');
        if (movieSelection) movieSelection = JSON.parse(movieSelection);
        else movieSelection = [];
        if (seriesSelection) seriesSelection = JSON.parse(seriesSelection);
        else seriesSelection = [];
        $("button.order, .button.order").removeClass('disabled').addClass('confirm');
        for (var i=0; i<movieSelection.length; i++) {
            $("button.order#" + movieSelection[i].id).removeClass('confirm').addClass('disabled');
            $("a.order#" + movieSelection[i].id).removeClass('confirm').addClass('disabled')
        }
        for (i=0; i<seriesSelection.length; i++) {
            $("button.order#" + seriesSelection[i].id).removeClass('confirm').addClass('disabled');
            $("a.order#" + seriesSelection[i].id).removeClass('confirm').addClass('disabled')
        }
    }

    c.removeFromCart = function(index, type) {
        var itemsCount = localStorage.getItem('itemsCount'),
            movieSelection = JSON.parse(localStorage.getItem('movieSelection')),
            seriesSelection = JSON.parse(localStorage.getItem('seriesSelection'));
        itemsCount = parseInt(itemsCount) - 1;
        if (type == 'movie') {
            var removedItem = movieSelection[index];
            movieSelection.splice(index, 1)
        } else {
            index -= movieSelection.length;
            var removedItem = movieSelection[index];
            seriesSelection.splice(index, 1)
        }
        c.latestDeletedElt = {
            item: removedItem,
            index: index
        };
        localStorage.setItem('itemsCount', itemsCount);
        localStorage.setItem('movieSelection', JSON.stringify(movieSelection));
        localStorage.setItem('seriesSelection', JSON.stringify(seriesSelection))
    };

    c.clearCart = function() {
        localStorage.setItem('itemsCount', 0);
        localStorage.setItem('movieSelection', '[]');
        localStorage.setItem('seriesSelection', '[]');
        c.populateCartPanel()
    };

    var call = Array(); //Keeps track of how often the endpoint has been queried, increments by one on each call
    c.search = function(endpoint, str, resultsSelector, resultItemSelector, spinnerSelector, templateFunction) {
        str = $.trim(str);
        if (!str || str.length < 2) {
            $(resultsSelector).hide();
            return
        }
        if ($(resultsSelector).css('display') == 'none') {
            $(resultItemSelector).not('.tpl').remove();
            $(resultsSelector).show()
        }
        $(spinnerSelector).show();
        call.push(0);
        var n = call.length;

        $.getJSON(endpoint, {q: str, format: 'json'}, function(data) {
            if (n < call.length) // Display results only if the call matches the number matches the length of call, meaning that we show results of only the latest call
                return;
            $(spinnerSelector).hide();
            $(resultItemSelector).not('.tpl').remove();
            if ((data.length) == 0) {
                $(resultsSelector + ' .no-result').show();
                return
            }
            $(resultsSelector + ' .no-result').hide();
            for (var i=0; i < data.length; i++) {
                var $tpl = $(resultItemSelector + '.tpl').clone().removeClass('tpl');
                if (!templateFunction)
                    applyMediaTemplate($tpl, data[i], str).insertAfter(resultItemSelector + '.tpl');
                else
                    templateFunction($tpl, data[i], str).insertAfter(resultItemSelector + '.tpl')
            }
        })
    };

    function applyCartContentTemplate($tpl, item) {
        $tpl.data({id: item.id, title: item.title, load: item.load, type: item.type});
        $tpl.css('background-image',  item.poster.small_url);
        $tpl.find('.name span:first').text(item.title);
        return $tpl
    }

    function applyMediaTemplate ($tplMovie, media, searchTag) {
        $tplMovie.data({id: media.id, price: media.price, load: media.load});
        if (searchTag) {
            if (media.type == 'movie')
                var href = "/movie/"+ media.slug;
            else
                var href = "/series/" + media.slug;
            $tplMovie.attr('href', href);
            $tplMovie.find('.poster').css('background-image', "url('" + media.poster.thumb_url +"')");
            var highlightedTitle = media.title.toLowerCase().replace(searchTag, '<b>' + searchTag + '</b>');
            var cleanedTags = c.stripArticles(media.tags);
            var titleTags = c.stripArticles(media.title);
            var minorTag = cleanedTags.replace(titleTags, '');
            var highlightedMinorTag = minorTag.replace(searchTag, '<b>' + searchTag + '</b>');
            if (media.type == 'movie')
                $tplMovie.find('.title span:first').html(highlightedTitle);
            else
                $tplMovie.find('.title span:first').html(highlightedTitle + " - saison " + media.season);
            $tplMovie.find('.minor-tag').html(highlightedMinorTag)
        } else {

            $tplMovie.find('.poster').css('background-image', "url('" + media.poster.small_url +"')");
            $tplMovie.find('.orders span:first').text(media.display_orders);
            if (media.type == 'movie')
                $tplMovie.find('.title span:first').text(media.title);
            else
                $tplMovie.find('.title span:first').text(media.title + " - season " + media.season)
        }
        if (media.type == 'movie') {
            $tplMovie.find('a.detail').attr('href', "/movie/"+ media.slug);
            $tplMovie.find('a.detail').attr('title', media.title);
            $tplMovie.find('.amount').text(media.price);
            $tplMovie.find('.order').attr('id', media.id).data({id: media.id, price: media.price, load: media.load,
                title: media.title, type: media.type, is_adult: media.is_adult, poster: "url('" + media.poster.small_url +"')"});
            $tplMovie.find('.play').data({'type': 'movie', 'id': media.id});
            if (media.trailer_slug)
                $tplMovie.find('.trailer').data({'type': 'trailer', 'id': media.id});
            else
                $tplMovie.find('.trailer').hide();
        } else {
            $tplMovie.find('a.detail').attr('href', "/series/" + media.slug);
            $tplMovie.find('a.detail').attr('title', media.title + " season "+ media.season);
            $tplMovie.find("a.button").attr('href',  "/series/" + media.slug).removeClass('order').show();
            $tplMovie.find('.trailer').hide();
        }
        return $tplMovie
    }

    c.hasEnoughBalance = function(load) {
       var usedQuota = ikwen.getUsedQuota();
       return ikwen.availableQuota > (parseInt(usedQuota) + parseInt(load));
    };

    c.getUsedQuota = function() {
        var movieSelection = localStorage.getItem('movieSelection'),
            seriesSelection = localStorage.getItem('seriesSelection'),
            moviesLoad = 0,
            seriesLoad = 0;
        if (movieSelection) {
            var data = JSON.parse(movieSelection);
            for(var i=0; i<data.length; i++){
                moviesLoad = parseInt(moviesLoad) + parseInt(data[i].load)
            }
        }
        if (seriesSelection) {
            var data = JSON.parse(seriesSelection);
            for(var j=0; j<data.length; j++) {
                seriesLoad = parseInt(seriesLoad) + parseInt(data[j].load)
            }
        }
        return moviesLoad + seriesLoad
    };

    c.listMovieForSave = function() {
        var movieSelection = localStorage.getItem('movieSelection');
        var seriesSelection = localStorage.getItem('seriesSelection');
        var movies = '';
        if (!movieSelection && !seriesSelection) movies = 'no movie';
        if (movieSelection) {
            var data = JSON.parse(movieSelection);
            for(var i = 0; i < data.length; i++) {
                movies += data[i].id + '|' + data[i].type + ','
            }
        }
        if (seriesSelection) {
            var data = JSON.parse(seriesSelection);
            for(var i = 0; i < data.length; i++) {
                movies += data[i].id + '|' + data[i].type + ','
            }
        }
        return movies
    };

    c.stripArticles = function(str) {
        var cleaned = tune(str.toLowerCase());
        cleaned = cleaned.replace(/^le /, "").replace(/ le /g, " ").replace(/^la /, "").replace(/ la /g, " ")
                    .replace(/^les /, "").replace(/ les /g, " ").replace(/l'/g, "")
                    .replace(/^un /, "").replace(/ un /g, " ").replace(/^une /, "").replace(/ une /g, " ")
                    .replace(/^des /, "").replace(/ des /g, " ").replace(/d'/g, "")
                    .replace(/^de /, "").replace(/ de /g, " ").replace(/^du /, "").replace(/ du /g, " ")
                    .replace(/^a /, "").replace(/ a /g, " ").replace(/^the /, "").replace(/ the /g, " ")
                    .replace(/^at /, "").replace(/ at /g, " ").replace(/ of /g, " ")
                    .replace(" 1", "").replace(" 2", "").replace(" 3", "").replace(" 4", "").replace(" 5", "")
                    .replace(" 6", "").replace(" 6", "").replace(" 7", "").replace(" 8", "").replace(" 9", "")
                    .replace(" - ", " ")
                    .replace("-", "")
                    .replace(".", "")
                    .replace(",", "")
                    .replace("_", "")
                    .replace("'", "");
        return cleaned;
    };

    function tune(text) {
        text = text.replace(/\\s{2,}/," ")
                       .replace('à', 'a')
                       .replace('â', 'a')
                       .replace('ä', 'a')
                       .replace('é', 'e')
                       .replace('è', 'e')
                       .replace('ê', 'e')
                       .replace('ë', 'e')
                       .replace('î', 'i')
                       .replace('ï', 'i')
                       .replace('ô', 'o')
                       .replace('ö', 'o')
                       .replace('û', 'u')
                       .replace('ü', 'u')
                       .replace('ù', 'u')
                       .replace('ç', 'c');
       return text
    }


    function applyHomeItemTemplate($tplMovie, media, is_main) {
        if (is_main) $tplMovie.find('.poster').css('background-image', "url('" + media.poster +"')");
        else  $tplMovie.find('.poster').css('background-image', "url('" + media.poster.small_url +"')");
        $tplMovie.find('.orders span:first').text(media.display_orders);
        $tplMovie.find('.clicks span:first').text(media.display_clicks);
        if (media.type == 'movie') {
            $tplMovie.find('.title').text(media.title);
            $tplMovie.find('.poster').attr('title', media.title  + ": " + media.display_load);
            $tplMovie.find('a.detail').attr('href', "/movie/"+ media.slug);
            $tplMovie.find('.price').text(media.price);
            $tplMovie.find('span.load').text(media.display_load);
            $tplMovie.find('.order').attr('id', media.id).data({id: media.id, price: media.price, load: media.load,
                title: media.title, type: media.type, is_adult: media.is_adult, poster: "url('" + media.poster.small_url +"')"});
            $tplMovie.find('.play').data({'type': 'movie', 'id': media.id});
            if (media.trailer_slug)
                $tplMovie.find('.trailer').data({'type': 'trailer', 'id': media.id});
            else
                $tplMovie.find('.trailer').remove();
        } else {
            $tplMovie.find('.title').text(media.title + " - saison " + media.season);
            $tplMovie.find('.poster').attr('title', media.title + " season "+ media.season);
            $tplMovie.find('a.detail').attr('href', "/series/" + media.slug);
            $tplMovie.find('span.load').text(media.display_load);
            $tplMovie.find("a.button").attr('href',  "/series/" + media.slug).removeClass('order').show();
            $tplMovie.find('.trailer').hide();
        }
        return $tplMovie
    }

    c.launchAutoSelection = function(endpoint, moviesLoad, seriesLoad) {
        $('form#auto-selection .spinner-container').show();
        $.getJSON(endpoint, {movies_max_load: moviesLoad, series_max_load: seriesLoad}, function(data) {
            $('form#auto-selection .spinner-container').hide();
            for (var i=0; i<data.length; i++) {
                var item = data[i];
                c.addToCart(item);
            }
            c.populateCartPanel();
        })
    }
})(ikwen);