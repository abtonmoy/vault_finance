# categories.py
# Shared constants and patterns

SPENDING_CATEGORIES = {
    'Food & Dining': {
        'restaurants': ['restaurant', 'cafe', 'bistro', 'diner', 'grill', 'kitchen', 'eatery', 'pizzeria', 'buffet'],
        'fast_food': ['mcdonalds', 'burger king', 'kfc', 'taco bell', 'subway', 'chipotle', 'panera', 'chick-fil-a'],
        'coffee': ['starbucks', 'dunkin', 'coffee', 'espresso', 'latte'],
        'delivery': ['doordash', 'ubereats', 'grubhub', 'postmates', 'seamless', 'delivery'],
        'bars': ['bar', 'pub', 'brewery', 'tavern', 'lounge', 'wine bar'],
        'dining': ['dining', 'food', 'pizza']
    },
    'Groceries': {
        'supermarkets': ['walmart', 'target', 'costco', 'sams club', 'bjs', 'aldi', 'food lion'],
        'organic': ['whole foods', 'sprouts', 'fresh market', 'trader joes'],
        'keywords': ['grocery', 'market', 'supermarket', 'food store', 'safeway', 'kroger', 'publix']
    },
    'Transportation': {
        'gas': ['shell', 'exxon', 'bp', 'chevron', 'mobil', 'citgo', 'gas station', 'fuel', 'gas'],
        'rideshare': ['uber', 'lyft', 'taxi', 'cab'],
        'parking': ['parking', 'garage', 'meter', 'valet'],
        'public_transport': ['metro', 'bus', 'train', 'transit', 'mta', 'bart'],
        'airlines': ['airline', 'airways', 'flight', 'delta', 'american airlines', 'united', 'southwest'],
        'car_services': ['oil change', 'tire', 'mechanic', 'auto repair', 'car wash']
    },
    'Shopping': {
        'online': ['amazon', 'ebay', 'paypal', 'apple.com', 'google play'],
        'department': ['target', 'walmart', 'kohls', 'jcpenney', 'sears', 'nordstrom'],
        'electronics': ['best buy', 'apple store', 'microsoft', 'gamestop', 'bestbuy'],
        'clothing': ['gap', 'old navy', 'h&m', 'zara', 'nike', 'adidas'],
        'home': ['home depot', 'lowes', 'ikea', 'bed bath beyond', 'pier 1'],
        'general': ['store', 'shop', 'retail', 'purchase', 'buy', 'mall', 'outlet']
    },
    'Bills & Utilities': {
        'utilities': ['electric', 'electricity', 'water', 'gas company', 'utility', 'bill', 'payment'],
        'telecom': ['verizon', 'att', 't-mobile', 'sprint', 'comcast', 'xfinity', 'internet', 'cable', 'phone'],
        'insurance': ['insurance', 'allstate', 'geico', 'progressive', 'state farm'],
        'housing': ['rent', 'mortgage', 'property management', 'hoa']
    },
    'Healthcare': {
        'medical': ['hospital', 'medical center', 'clinic', 'doctor', 'physician', 'medical', 'health'],
        'pharmacy': ['cvs', 'walgreens', 'rite aid', 'pharmacy', 'prescription'],
        'dental': ['dental', 'dentist', 'orthodontist'],
        'vision': ['eye care', 'optometry', 'vision', 'eyeglasses']
    },
    'Entertainment': {
        'streaming': ['netflix', 'hulu', 'disney+', 'amazon prime', 'spotify', 'apple music'],
        'movies': ['movie', 'cinema', 'theater', 'amc', 'regal'],
        'gaming': ['steam', 'playstation', 'xbox', 'nintendo', 'gaming', 'game'],
        'fitness': ['gym', 'fitness', 'yoga', 'pilates', 'planet fitness', '24 hour fitness']
    },
    'Banking & Fees': {
        'fees': ['fee', 'charge', 'overdraft', 'maintenance', 'service charge', 'wire fee'],
        'atm': ['atm', 'cash withdrawal', 'atm fee'],
        'interest': ['interest charge', 'finance charge', 'late fee']
    },
    'Income': {
        'salary': ['payroll', 'salary', 'direct deposit', 'paycheck', 'wages'],
        'other': ['refund', 'tax refund', 'dividend', 'interest earned', 'cashback', 'reward', 'deposit', 'reversal', 'return', 'credit', 'income']
    },
    'Personal Care': {
        'beauty': ['salon', 'spa', 'barber', 'nail', 'massage'],
        'products': ['cosmetics', 'skincare', 'shampoo']
    },
    'Education': {
        'tuition': ['university', 'college', 'school', 'tuition'],
        'supplies': ['bookstore', 'textbook', 'school supply']
    },
    'Travel': {
        'hotels': ['hotel', 'motel', 'resort', 'airbnb', 'booking.com'],
        'transport': ['airline', 'train', 'bus ticket', 'car rental']
    }
}

