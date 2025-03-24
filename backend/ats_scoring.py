import re
from collections import Counter
from typing import Dict, List, Tuple, Union

class ATSScanner:
    """Comprehensive ATS scoring system with domain-specific rules"""
    
    # Domain-specific keyword libraries
    DOMAIN_KEYWORDS = {
        'software engineering': [
            'python', 'java', 'javascript', 'c++', 'git', 
            'docker', 'kubernetes', 'aws', 'backend', 'frontend',
            'algorithm', 'database', 'rest api', 'microservices'
        ],
        'data science': [
            'python', 'r', 'sql', 'pandas', 'numpy', 
            'machine learning', 'deep learning', 'tensorflow',
            'pytorch', 'statistics', 'data visualization',
            'big data', 'spark', 'hadoop'
        ],
        'product management': [
            'agile', 'scrum', 'jira', 'roadmap', 'user stories',
            'market research', 'product lifecycle', 'go-to-market',
            'customer journey', 'kpis', 'metrics', 'wireframing'
        ]
    }

    # Industry-standard action verbs
    ACTION_VERBS = [
        'developed', 'implemented', 'designed', 'led', 
        'optimized', 'increased', 'reduced', 'achieved',
        'launched', 'managed', 'collaborated', 'automated'
    ]

    # Common resume typos to detect
    COMMON_TYPOS = [
        'teh', 'adn', 'recieve', 'experiance', 
        'acheive', 'skils', 'responsiblities'
    ]
    
    @classmethod
    def calculate_score(cls, resume_data: Dict) -> Dict[str, Union[int, List[str], Dict]]:
        try:
            score = 0
            feedback = []
            domain = resume_data.get('domain', '').lower()

            # 1. Keyword Analysis (40 points max)
            keyword_score, kw_feedback = cls._analyze_keywords(resume_data, domain)
            score += keyword_score
            feedback.extend(kw_feedback)

            # 2. Resume Completeness (30 points)
            completeness_score, comp_feedback = cls._check_completeness(resume_data)
            score += completeness_score
            feedback.extend(comp_feedback)

            # 3. Content Quality (20 points)
            quality_score, quality_feedback = cls._check_content_quality(resume_data)
            score += quality_score
            feedback.extend(quality_feedback)

            # 4. Red Flags (0-10 points deduction)
            red_flags, red_feedback = cls._detect_red_flags(resume_data)
            score = max(0, score - red_flags)
            feedback.extend(red_feedback)

            # New: Calculate matched keywords based on domain-specific keywords
            import re
            from collections import Counter
            content = cls._get_content_string(resume_data)
            word_freq = Counter(re.findall(r'\w+', content.lower()))
            matched_keywords = [kw for kw in cls.DOMAIN_KEYWORDS.get(domain, []) if word_freq[kw] > 0]

            return {
                "ats_score": min(100, round(score)),
                "feedback": feedback,
                "matched_keywords": matched_keywords,
                "keyword_analysis": cls._get_keyword_analysis(resume_data, domain)
            }

        except Exception as e:
            return {"error": f"ATS calculation failed: {str(e)}"}


    @classmethod
    def _analyze_keywords(cls, data: Dict, domain: str) -> Tuple[int, List[str]]:
        """Analyze keyword frequency and relevance"""
        keywords = cls.DOMAIN_KEYWORDS.get(domain, [])
        content = cls._get_content_string(data)
        word_freq = Counter(re.findall(r'\w+', content.lower()))
        
        # Score calculation
        keyword_score = sum(min(3, word_freq[kw]) for kw in keywords)
        normalized_score = min(40, (keyword_score / len(keywords)) * 40) if keywords else 20
        
        # Feedback
        matched_kw = [(kw, word_freq[kw]) for kw in keywords if word_freq[kw] > 0]
        feedback = [
            f"Keyword score: {normalized_score:.1f}/40",
            f"Matched {len(matched_kw)}/{len(keywords)} domain keywords"
        ]
        
        return normalized_score, feedback

    @classmethod
    def _check_completeness(cls, data: Dict) -> Tuple[int, List[str]]:
        """Check for required resume sections"""
        required_sections = [
            ('name', 5, "Full name"),
            ('title', 5, "Job title"),
            ('summary', 5, "Professional summary"),
            ('workExperience', 10, "Work experience"),
            ('skills', 5, "Skills list"),
            ('education', 5, "Education section")
        ]
        
        score = 0
        feedback = []
        
        for field, points, name in required_sections:
            if data.get(field):
                if field == 'workExperience' and len(data[field]) > 0:
                    score += points
                elif field != 'workExperience':
                    score += points
            else:
                feedback.append(f"Missing: {name}")
        
        return score, feedback

    @classmethod
    def _check_content_quality(cls, data: Dict) -> Tuple[int, List[str]]:
        """Evaluate content effectiveness"""
        descriptions = ' '.join(
            exp.get('description', '') 
            for exp in data.get('workExperience', [])
        ).lower()
        
        # Action verbs
        verb_count = sum(
            1 for verb in cls.ACTION_VERBS 
            if verb in descriptions
        )
        verb_score = min(10, verb_count * 2)
        
        # Quantifiable results
        quantifiers = len(re.findall(
            r'\d+%|\$?\d+\+?|[\d,]+', 
            descriptions
        ))
        quant_score = min(10, quantifiers * 2)
        
        feedback = [
            f"Action verbs: {verb_count} ({verb_score}/10)",
            f"Quantifiable results: {quantifiers} ({quant_score}/10)"
        ]
        
        return verb_score + quant_score, feedback

    @classmethod
    def _detect_red_flags(cls, data: Dict) -> Tuple[int, List[str]]:
        """Identify resume red flags"""
        content = cls._get_content_string(data)
        red_flags = 0
        feedback = []
        
        # Typos detection
        typo_count = sum(
            1 for typo in cls.COMMON_TYPOS 
            if typo in content.lower()
        )
        if typo_count > 0:
            red_flags += min(5, typo_count)
            feedback.append(f"Found {typo_count} potential typos")
        
        # Skills spam check
        if len(data.get('skills', [])) > 25:
            red_flags += 5
            feedback.append("Too many skills (may trigger spam filters)")
        
        return red_flags, feedback

    @classmethod
    def _get_content_string(cls, data: Dict) -> str:
        """Combine all textual resume content"""
        return ' '.join([
            data.get('title', ''),
            data.get('summary', ''),
            ' '.join(data.get('skills', [])),
            ' '.join(exp.get('description', '') 
                   for exp in data.get('workExperience', []))
        ])

    @classmethod
    def _get_keyword_analysis(cls, data: Dict, domain: str) -> Dict:
        """Generate detailed keyword report"""
        content = cls._get_content_string(data)
        words = re.findall(r'\w+', content.lower())
        word_freq = Counter(words)
        
        # Filter out stopwords
        stopwords = {'the', 'and', 'with', 'for', 'that', 'this'}
        meaningful_words = {
            k: v for k, v in word_freq.items() 
            if k not in stopwords and len(k) > 3
        }
        
        return {
            "domain_keywords": cls.DOMAIN_KEYWORDS.get(domain, []),
            "top_keywords": dict(Counter(meaningful_words).most_common(10)),
            "action_verbs_found": [
                verb for verb in cls.ACTION_VERBS 
                if verb in word_freq
            ]
        }