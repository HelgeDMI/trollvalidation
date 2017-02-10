"""
Validation decorators
"""
import time
import logging
from functools import wraps
from funcsigs import signature
from collections import namedtuple


LOG = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG,
#                     format='[%(levelname)s: %(asctime)s: %(name)s] %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S')


PreReturn = namedtuple('PreReturn', 'tmpfiles data_ref data_test')


def timethis(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        d_time = end_time - start_time
        ref_time = args[0]
        LOG.info("Validation for {0} took {1}s.".format(ref_time, d_time))
        return result

    return wrapper


def around_step(pre_func=None, post_func=None):

    def pre_actions(*args, **kwargs):
        if not pre_func:
            raise NotImplementedError('You have to provide an implementation'  
                                      'for the pre-validation step!')
        return pre_func(*args, **kwargs)

    def post_actions(*args, **kwargs):
        if post_func:
            return post_func(*args, **kwargs)
        else:
            raise NotImplementedError('You have to provide an implementation'  
                                      'for the post-validation step!')

    def decorate(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                ref_time, ice_chart_file, product_file = args[0], args[1], args[2]
                results = pre_actions(ref_time, ice_chart_file, product_file)

                temp_files = results.tmpfiles
                data_ref, data_test = results.data_ref, results.data_test

                results = func(ref_time, data_ref, data_test)
                post_actions(results, temp_files.tmpfiles)

                return results
            except Exception, e:
                LOG.debug('Error with around_step decorator')
                LOG.exception(e)

        return wrapper

    return decorate


def around_task(pre_func=None, post_func=None):

    def pre_actions(*args, **kwargs):
        if not pre_func:
            raise NotImplementedError('You have to provide an implementation'
                                      'for the pre-validation step!')
        new_kwargs = {}
        sig = signature(pre_func).parameters
        for idx, (k, v) in enumerate(sig.iteritems()):
            if k in kwargs.keys():
                new_kwargs[k] = kwargs[k]

        return pre_func(*args, **new_kwargs)

    def post_actions(results, **kwargs):
        if not post_func:
            raise NotImplementedError('You have to provide an implementation'
                                      'for the post-validation step!')

        new_kwargs = {}
        sig = signature(post_func).parameters
        for idx, (k, v) in enumerate(sig.iteritems()):
            if idx > 0:
                if k in kwargs.keys():
                    new_kwargs[k] = kwargs[k]
                # else:
                #     new_args.append(v)
        return post_func(results, **new_kwargs)

    def decorate(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            results = pre_actions(*args, **kwargs)
            results = func(results, **kwargs)
            post_actions(results, **kwargs)

            return results

        return wrapper

    return decorate


# def pre(func=None):
#
#     def pre_actions(*args, **kwargs):
#         if not func:
#             raise NotImplementedError('You have to provide an implementation'
#                                       'for the pre-validation step!')
#         new_kwargs = {}
#         sig = signature(func).parameters
#         for idx, (k, v) in enumerate(sig.iteritems()):
#             if k in kwargs.keys():
#                 new_kwargs[k] = kwargs[k]
#
#         return func(*args, **new_kwargs)
#
#     def decorate(body_func):
#
#         @wraps(body_func)
#         def wrapper(*args, **kwargs):
#             results = pre_actions(*args, **kwargs)
#             results = body_func(results, **kwargs)
#             return results
#
#         return wrapper
#
#     return decorate
#
#
# from funcsigs import signature
#
#
# def post(func):
#     def post_actions(results, **kwargs):
#         if not func:
#             raise NotImplementedError('You have to provide an implementation'
#                                       'for the pre-validation step!')
#         # new_args = []
#         new_kwargs = {}
#         sig = signature(func).parameters
#         for idx, (k, v) in enumerate(sig.iteritems()):
#             if idx > 0:
#                 if k in kwargs.keys():
#                     new_kwargs[k] = kwargs[k]
#                 # else:
#                 #     new_args.append(v)
#         return func(results, **new_kwargs)
#
#     def decorate(body_func):
#
#         @wraps(body_func)
#         def wrapper(*args, **kwargs):
#             results = body_func(*args, **kwargs)
#             post_actions(results, **kwargs)
#             return results
#
#         return wrapper
#
#     return decorate
