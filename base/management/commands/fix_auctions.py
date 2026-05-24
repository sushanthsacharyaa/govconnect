# base/management/commands/fix_auctions.py
from django.core.management.base import BaseCommand
from base.models import Auction, Bid

class Command(BaseCommand):
    help = 'Fix auction data - sync current_highest_bid with actual bids'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Fixing Auction Data...'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        auctions = Auction.objects.all()
        fixed_count = 0
        
        for auction in auctions:
            self.stdout.write(f'\nProcessing auction: {auction.auction_title}')
            
            # Get highest bid
            highest_bid = auction.bids.filter(bid_status='WINNING').order_by('-bid_amount').first()
            
            if highest_bid:
                if auction.current_highest_bid != highest_bid.bid_amount:
                    self.stdout.write(f'  Updating current_highest_bid from {auction.current_highest_bid} to {highest_bid.bid_amount}')
                    auction.current_highest_bid = highest_bid.bid_amount
                    auction.save()
                    fixed_count += 1
                else:
                    self.stdout.write(f'  current_highest_bid already correct: {auction.current_highest_bid}')
            else:
                if auction.current_highest_bid != auction.reserve_price:
                    self.stdout.write(f'  Setting current_highest_bid from {auction.current_highest_bid} to reserve price {auction.reserve_price}')
                    auction.current_highest_bid = auction.reserve_price
                    auction.save()
                    fixed_count += 1
                else:
                    self.stdout.write(f'  current_highest_bid already correct: {auction.current_highest_bid}')
            
            # Ensure only one winning bid
            winning_bids = auction.bids.filter(bid_status='WINNING')
            if winning_bids.count() > 1:
                self.stdout.write(self.style.WARNING(f'  WARNING: Found {winning_bids.count()} winning bids! Fixing...'))
                highest = winning_bids.order_by('-bid_amount').first()
                for bid in winning_bids:
                    if bid.id != highest.id:
                        bid.bid_status = 'LOST'
                        bid.save()
                        self.stdout.write(f'    Changed bid {bid.id} from WINNING to LOST')
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS(f'Data fix completed! {fixed_count} auctions were fixed.'))
        self.stdout.write(self.style.SUCCESS('=' * 60))