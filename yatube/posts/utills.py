from django.core.paginator import Paginator

COUNT_POST = 10


def get_paginator(request, queryset):
    paginator = Paginator(queryset, COUNT_POST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj
    }
