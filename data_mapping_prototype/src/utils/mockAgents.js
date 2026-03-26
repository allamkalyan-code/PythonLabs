
// Mock Canonical Schema for the prototype
export const CANONICAL_SCHEMA = [
    { field: 'loan_number', type: 'string', description: 'Unique identifier for the loan' },
    { field: 'member_number', type: 'string', description: 'Member identifier' },
    { field: 'loan_amount', type: 'number', description: 'Principal balance or amount' },
    { field: 'interest_rate', type: 'number', description: 'Annual interest rate' },
    { field: 'loan_status', type: 'string', description: 'Current status (Active, Paid, etc.)' },
    { field: 'origination_date', type: 'date', description: 'Date the loan was opened' },
    // source_system is usually metadata, but we can treat as field if needed
];

// Agent 1: Logic to detect schema from JSON
export const detectSchema = (data, vendorName) => {
    if (!data || data.length === 0) return [];
    const sample = data[0];

    return Object.keys(sample).map(key => {
        const val = sample[key];
        let type = typeof val;
        let semantic = 'Unknown';

        // Simple heuristics
        if (key.includes('id') || key.includes('number') || key.includes('acct')) semantic = 'Identifier';
        if (key.includes('amt') || key.includes('bal') || key.includes('amount')) semantic = 'Financial Amount';
        if (key.includes('rate') || key.includes('int') || key.includes('rt')) semantic = 'Percentage/Rate';
        if (key.includes('sts') || key.includes('state') || key.includes('code')) semantic = 'Status Code';

        return {
            vendor: vendorName,
            column: key,
            type: type,
            sample: val,
            inferred_semantic: semantic
        };
    });
};

// Agent 2: Logic to suggest mappings
export const suggestMapping = (detectedSchema) => {
    return detectedSchema.map(item => {
        let bestMatch = null;
        let score = 0;

        // Simulate AI "Understanding" with hardcoded logic for the demo data
        if (['loan_id', 'acct_n', 'loan_number'].includes(item.column)) {
            bestMatch = 'loan_number';
            score = 0.95;
        } else if (['amount', 'bal', 'principal'].includes(item.column)) {
            bestMatch = 'loan_amount';
            score = 0.92;
        } else if (['rate', 'int_rt'].includes(item.column)) {
            bestMatch = 'interest_rate';
            score = 0.89;
        } else if (['sts', 'state', 'status'].includes(item.column)) {
            bestMatch = 'loan_status';
            score = 0.85;
        }

        // Drift / No Match
        if (!bestMatch) {
            return {
                ...item,
                suggested_canonical: null,
                confidence: 0.1,
                status: 'UNMAPPED'
            };
        }

        return {
            ...item,
            suggested_canonical: bestMatch,
            confidence: score,
            status: 'PENDING_REVIEW'
        };
    });
};

// Agent 3: Logic to detect new/drift fields
export const detectDrift = (mappings) => {
    return mappings.filter(m => m.status === 'UNMAPPED' || m.confidence < 0.5);
};
