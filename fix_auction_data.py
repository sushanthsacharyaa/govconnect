# fix_auction_data.py
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from base.models import Auction, Bid
from django.db import transaction

def fix_auction_data():
    """
    Fix existing auction data:
    1. Set current_highest_bid for all auctions
    2. Ensure winning bids are properly marked
    3. Sync current_highest_bid with actual winning bids
    """
    print("=" * 60)
    print("Fixing Auction Data...")
    print("=" * 60)
    
    auctions = Auction.objects.all()
    total_auctions = auctions.count()
    print(f"Found {total_auctions} auctions to process")
    
    fixed_count = 0
    error_count = 0
    
    for auction in auctions:
        try:
            print(f"\n--- Processing Auction {auction.id}: {auction.auction_title} ---")
            
            # Get the highest bid for this auction
            highest_bid = auction.bids.filter(bid_status='WINNING').order_by('-bid_amount').first()
            
            if highest_bid:
                # If there's a winning bid, use its amount
                current_value = auction.current_highest_bid
                if current_value != highest_bid.bid_amount:
                    print(f"  Updating current_highest_bid from {current_value} to {highest_bid.bid_amount}")
                    auction.current_highest_bid = highest_bid.bid_amount
                    auction.save(update_fields=['current_highest_bid'])
                    fixed_count += 1
                else:
                    print(f"  current_highest_bid already correct: {current_value}")
            else:
                # No bids yet, set to reserve price
                current_value = auction.current_highest_bid
                if current_value is None or current_value == 0 or current_value != auction.reserve_price:
                    print(f"  No bids yet. Setting current_highest_bid from {current_value} to reserve price {auction.reserve_price}")
                    auction.current_highest_bid = auction.reserve_price
                    auction.save(update_fields=['current_highest_bid'])
                    fixed_count += 1
                else:
                    print(f"  current_highest_bid already correct: {current_value}")
            
            # Ensure only one winning bid per auction
            winning_bids = auction.bids.filter(bid_status='WINNING')
            if winning_bids.count() > 1:
                print(f"  WARNING: Found {winning_bids.count()} winning bids! Fixing...")
                # Keep only the highest bid as WINNING
                highest = winning_bids.order_by('-bid_amount').first()
                for bid in winning_bids:
                    if bid.id != highest.id:
                        bid.bid_status = 'LOST'
                        bid.save(update_fields=['bid_status'])
                        print(f"    Changed bid {bid.id} from WINNING to LOST")
            
            # Ensure bids are properly ordered
            all_bids = auction.bids.all().order_by('-bid_amount')
            for idx, bid in enumerate(all_bids):
                if idx == 0 and bid.bid_status != 'WINNING':
                    print(f"  Setting highest bid {bid.id} to WINNING")
                    bid.bid_status = 'WINNING'
                    bid.save(update_fields=['bid_status'])
                elif idx > 0 and bid.bid_status == 'WINNING':
                    print(f"  Setting outbid {bid.id} to LOST")
                    bid.bid_status = 'LOST'
                    bid.save(update_fields=['bid_status'])
                    
        except Exception as e:
            print(f"  ERROR processing auction {auction.id}: {str(e)}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print("FIX COMPLETE")
    print("=" * 60)
    print(f"Total auctions processed: {total_auctions}")
    print(f"Auctions fixed: {fixed_count}")
    print(f"Errors encountered: {error_count}")
    print("=" * 60)

def verify_auction_data():
    """
    Verify that all auction data is correct
    """
    print("\n" + "=" * 60)
    print("VERIFYING AUCTION DATA")
    print("=" * 60)
    
    auctions = Auction.objects.all()
    issues_found = False
    
    for auction in auctions:
        highest_bid = auction.bids.filter(bid_status='WINNING').order_by('-bid_amount').first()
        
        # Check 1: current_highest_bid should not be None or 0
        if auction.current_highest_bid is None or auction.current_highest_bid == 0:
            print(f"❌ Auction {auction.id}: current_highest_bid is {auction.current_highest_bid} (should be {auction.reserve_price})")
            issues_found = True
        elif highest_bid and auction.current_highest_bid != highest_bid.bid_amount:
            print(f"❌ Auction {auction.id}: current_highest_bid ({auction.current_highest_bid}) doesn't match highest bid ({highest_bid.bid_amount})")
            issues_found = True
        elif not highest_bid and auction.current_highest_bid != auction.reserve_price:
            print(f"❌ Auction {auction.id}: current_highest_bid ({auction.current_highest_bid}) doesn't match reserve price ({auction.reserve_price})")
            issues_found = True
        else:
            print(f"✅ Auction {auction.id}: OK - current_highest_bid = {auction.current_highest_bid}")
    
    if not issues_found:
        print("\n✅ All auction data is correct!")
    else:
        print("\n⚠️ Issues found. Run fix_auction_data() again.")
    
    print("=" * 60)

def show_auction_summary():
    """
    Display a summary of all auctions
    """
    print("\n" + "=" * 60)
    print("AUCTION SUMMARY")
    print("=" * 60)
    
    auctions = Auction.objects.all()
    
    for auction in auctions:
        bid_count = auction.bids.count()
        winning_bid = auction.bids.filter(bid_status='WINNING').first()
        
        print(f"\n📊 Auction ID: {auction.id}")
        print(f"   Title: {auction.auction_title}")
        print(f"   Status: {auction.auction_status}")
        print(f"   Reserve Price: ₹{auction.reserve_price:,.2f}")
        print(f"   Current Highest Bid: ₹{auction.current_highest_bid:,.2f}")
        print(f"   Total Bids: {bid_count}")
        
        if winning_bid:
            print(f"   Winning Bidder: {winning_bid.bidder.username}")
            print(f"   Winning Amount: ₹{winning_bid.bid_amount:,.2f}")
        else:
            print(f"   No bids yet")
        
        if auction.is_live():
            print(f"   🔴 LIVE - Ends at: {auction.auction_end_time}")
        elif auction.auction_status == 'UPCOMING':
            print(f"   🟡 UPCOMING - Starts at: {auction.auction_start_time}")
        else:
            print(f"   ⚫ ENDED")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    print("\n" + "█" * 60)
    print("AUCTION DATA FIX TOOL")
    print("█" * 60)
    
    # Step 1: Show current summary
    show_auction_summary()
    
    # Step 2: Fix the data
    fix_auction_data()
    
    # Step 3: Verify the fixes
    verify_auction_data()
    
    # Step 4: Show updated summary
    show_auction_summary()
    
    print("\n✅ Data fix completed successfully!")