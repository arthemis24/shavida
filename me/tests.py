# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from django.test import TestCase
from ikwen.models import Member
from reporting.models import CVBOrder
from sales.models import RetailPrepayment


class SimpleTest(TestCase):

    def test_is_first_refill_with_member_who_never_refilled(self):
        customer = Member.objects.create_user(account_type=Member.CUSTOMER, username='77777777', password='123456',
                                           email='roddy@red.com', postpaid_plan=None,
                                           storage_provider='CVB')
        self.assertTrue(customer.is_first_refill)

    # def test_is_first_refill_with_member_who_refilled_once(self):
    #     prepaid_plan = PrepaidPlan(id=2, name='plan1', cost=5000)
    #     storage = Storage(name='storage', size=32000, size_label=32000, type=Storage.FLASH_DISK)
    #     prepaid_plan.save()
    #     storage.save()
    #     customer = Member.objects.create_user(account_type=Member.CUSTOMER, username='77777777', password='123456',
    #                                        email='roddy@red.com', postpaid_plan=None, prepaid_plan=prepaid_plan,
    #                                        storage_provider='CVB', storage_status=Storage.ACQUIRING)
    #     when = datetime.now() - timedelta(days=12)
    #     latest_prepayment = RetailPrepayment(member=customer, when=when, amount=5000, storage=storage, duration=30, balance=20000)
    #     latest_prepayment.save()
    #     self.assertFalse(customer.can_order_adult)

    def test_can_order_adult_with_member_having_prepaid_plan_and_max_orders_reached(self):
        customer = Member.objects.create_user(account_type=Member.CUSTOMER, username='77777777', password='123456',
                                           email='roddy@red.com', postpaid_plan=None,
                                           storage_provider='CVB' )
        latest_prepayment = RetailPrepayment(member=customer, amount=5000, duration=30, balance=20000)
        latest_prepayment.save()
        for i in range(4):
            order = CVBOrder(member=customer, cost=5000, status=CVBOrder.PENDING,
                             storage_amount=0, movies_amount=0, delivery_amount=0,copy_amount=0)
            order.save()
        self.assertTrue(customer.can_order_adult)

    def test_can_order_adult_with_member_having_prepaid_plan_and_max_orders_not_reached(self):
        customer = Member.objects.create_user(account_type=Member.CUSTOMER, username='77777777', password='123456',
                                           email='roddy@red.com', postpaid_plan=None,
                                           storage_provider='CVB')
        latest_prepayment = RetailPrepayment(member=customer, amount=5000, duration=30, balance=20000)
        latest_prepayment.save()
        for i in range(2):
            order = CVBOrder(member=customer, cost=5000,  status=CVBOrder.PENDING,
                             storage_amount=0, movies_amount=0, delivery_amount=0,copy_amount=0)
            order.save()
        self.assertFalse(customer.can_order_adult)

    def test_can_order_adult_with_member_having_prepaid_plan_and_prepayment_expired(self):
        customer = Member.objects.create_user(account_type=Member.CUSTOMER, username='77777777', password='123456',
                                           email='roddy@red.com', postpaid_plan=None,
                                           storage_provider='CVB')
        when = datetime.now() - timedelta(days=40)
        latest_prepayment = RetailPrepayment(member=customer, when=when, amount=5000, duration=30, balance=20000)
        latest_prepayment.save()
        self.assertTrue(customer.can_order_adult)

    def test_can_order_adult_with_member_having_prepaid_plan_and_prepayment_not_expired(self):
        customer = Member.objects.create_user(account_type=Member.CUSTOMER, username='77777777', password='123456',
                                           email='roddy@red.com', postpaid_plan=None,
                                           storage_provider='CVB')
        when = datetime.now() - timedelta(days=12)
        latest_prepayment = RetailPrepayment(member=customer, when=when, amount=5000, duration=30, balance=20000)
        latest_prepayment.save()
        self.assertFalse(customer.can_order_adult)


