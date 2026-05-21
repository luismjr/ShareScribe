#!/usr/bin/env perl
#
# process.pl — ShareScribe transaction processor
#
# Reads raw transaction CSV, calculates per-shareholder per-ticker summaries:
#   - total shares bought / sold
#   - net position
#   - total invested, total proceeds, realised gain/loss
#   - total dividends received
#   - average cost basis
#
# Writes results to data/summary.csv for the PDF generation stage.

use strict;
use warnings;
use POSIX qw(strftime);

my $TXN_CSV     = "data/transactions.csv";
my $SUMMARY_CSV = "data/summary.csv";

open(my $in, "<", $TXN_CSV) or die "Cannot open $TXN_CSV: $!";

my %data;   # $data{account}{ticker} = { ... }
my %names;  # account -> shareholder name

my $header = <$in>;  # skip header line
chomp $header;

while (my $line = <$in>) {
    chomp $line;
    my ($txn_id, $account, $name, $ticker, $type,
        $shares, $price, $amount, $date) = split(/,/, $line);

    $names{$account} = $name;

    unless (exists $data{$account}{$ticker}) {
        $data{$account}{$ticker} = {
            shares_bought  => 0,
            shares_sold    => 0,
            total_invested => 0,
            total_proceeds => 0,
            dividends      => 0,
            txn_count      => 0,
        };
    }

    my $d = $data{$account}{$ticker};
    $d->{txn_count}++;

    if ($type eq "BUY") {
        $d->{shares_bought}  += $shares;
        $d->{total_invested} += $amount;
    } elsif ($type eq "SELL") {
        $d->{shares_sold}    += $shares;
        $d->{total_proceeds} += $amount;
    } elsif ($type eq "DIVIDEND") {
        $d->{dividends} += $amount;
    }
}
close($in);

open(my $out, ">", $SUMMARY_CSV) or die "Cannot open $SUMMARY_CSV: $!";

print $out join(",", qw(
    account name ticker
    shares_bought shares_sold net_shares
    total_invested total_proceeds realised_gain_loss
    dividends avg_cost_basis txn_count
)) . "\n";

for my $account (sort keys %data) {
    my $name = $names{$account};
    for my $ticker (sort keys %{ $data{$account} }) {
        my $d = $data{$account}{$ticker};

        my $net_shares = $d->{shares_bought} - $d->{shares_sold};
        my $realised   = $d->{total_proceeds} - $d->{total_invested};
        my $avg_cost   = $d->{shares_bought} > 0
                         ? $d->{total_invested} / $d->{shares_bought}
                         : 0;

        printf $out "%s,%s,%s,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%d\n",
            $account, $name, $ticker,
            $d->{shares_bought}, $d->{shares_sold}, $net_shares,
            $d->{total_invested}, $d->{total_proceeds}, $realised,
            $d->{dividends}, $avg_cost, $d->{txn_count};
    }
}

close($out);
print "Processing complete. Summary written to $SUMMARY_CSV\n";
