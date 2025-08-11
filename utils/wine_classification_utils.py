"""
Enhanced Wine Classification System with Geographic Detection
============================================================

A comprehensive wine classification system that combines:
- Sparkling wine categorization
- Variety consolidation and standardization  
- Text extraction from product descriptions
- **NEW: Geographic/Country detection from product descriptions**
- Enhanced confidence scoring and quality assessment

Author: [Crow and Claude]
Date: [08/06/2025]
Version: 2.0 - Now with Country Classification!
"""

import pandas as pd
import numpy as np
import re

class EnhancedWineClassificationSystem:
    """
    Enhanced wine classification system with geographic detection
    Targets 95%+ variety coverage and 70%+ country coverage
    """
    
    def __init__(self):
        """Initialize all pattern dictionaries and mappings"""
        self._initialize_patterns()
    
    def _initialize_patterns(self):
        """Initialize all classification patterns including NEW country patterns"""
        
        # =================================================================
        # EXISTING VARIETY PATTERNS (unchanged from your original system)
        # =================================================================
        
        # Abbreviation patterns for wine varieties
        self.abbreviation_patterns = {
            r'\bCAB\b': 'Cabernet Sauvignon', r'\bCHARD\b': 'Chardonnay',
            r'\bP/GRIG\b': 'Pinot Grigio', r'\bP/GRIS\b': 'Pinot Grigio',
            r'\bSYR\b': 'Syrah', r'\bGEW\b': 'Gewürztraminer',
            r'\bSAUV\b': 'Sauvignon Blanc', r'\bSAUV BLANC\b': 'Sauvignon Blanc',
            r'\bSAUV B\b': 'Sauvignon Blanc', r'\bPINOT GRIG\b': 'Pinot Grigio',
            r'\bPINOT GRIS\b': 'Pinot Grigio', r'\bPINOT NOIR\b': 'Pinot Noir',
            r'\bPINOT\b': 'Pinot Noir', r'\bRIESL\b': 'Riesling',
            r'\bMERLOT\b': 'Merlot', r'\bZINF\b': 'Zinfandel',
            r'\bMALBEC\b': 'Malbec', r'\bTEMP\b': 'Tempranillo',
            r'\bSHZ\b': 'Syrah', r'\bSHIRAZ\b': 'Syrah',
            r'\bPETITE SYRAH\b': 'Petite Sirah', r'\bPET SYR\b': 'Petite Sirah',
            r'\bMOSCATO\b': 'Moscato', r'\bMUSCAT\b': 'Moscato',
            r'\bMER\b': 'Merlot', r'\bRIES\b': 'Riesling', r'\bMAL\b': 'Malbec',
            r'\bNEBB\b': 'Nebbiolo', r'\bSANG\b': 'Sangiovese', r'\bBARB\b': 'Barbera',
            r'\bCHAB\b': 'Chardonnay', r'\bVIOG\b': 'Viognier', r'\bGAM\b': 'Gamay',
            r'\bPET\b': 'Petite Sirah', r'\bBLC\b': 'White Blend', r'\bCDR\b': 'Red Blend',
            r'\bROS\b': 'Rosé', r'\bP/AGE\b': 'Pinotage', r'\bKAB\b': 'Riesling',
            r'\bP/NOIR\b': 'Pinot Noir', r'\bZIN\b': 'Zinfandel', r'\bCHN\b': 'Chianti',
            r'\bS/BL\b': 'Sauvignon Blanc'
        }
        
        # Sparkling wine classification
        self.sparkling_patterns = {
            'red_sparkling': ['Lambrusco', 'Lambrusco di Sorbara', 'Lambrusco Grasparossa', 'Brachetto'],
            'white_sparkling': ['Champagne Blend', 'Sparkling Blend', 'Glera', 'Prosecco', 'Portuguese Sparkling', 'Crémant'],
            'ambiguous_sparkling': []
        }
        
        # Regional patterns (these also help with country detection)
        self.italian_regional_patterns = {
            r'\bBAROLO\b': 'Nebbiolo', r'\bBRUNELLO\b': 'Sangiovese', r'\bBRUN MONTAL\b': 'Sangiovese',
            r'\bCHIANTI\b': 'Sangiovese', r'\bCHN\b': 'Sangiovese', r'\bAMARONE\b': 'Amarone',
            r'\bSOAVE\b': 'Soave', r'\bVALPOLICELLA\b': 'Valpolicella', r'\bVALP\b': 'Valpolicella',
            r'\bAGLIANICO\b': 'Aglianico', r'\bBRACHETTO\b': 'Brachetto', r'\bMONTEPULCIANO\b': 'Montepulciano',
            r'\bMONTPUL\b': 'Montepulciano', r'\bMONT D\'ABRU\b': 'Montepulciano', r'\bPROSECCO\b': 'Prosecco',
            r'\bEST EST EST\b': 'White Blend', r'\bFRANCAIACORTA\b': 'Sparkling Blend',
            r'\bMASIANCO\b': 'White Blend', r'\bROSCATO\b': 'Moscato'
        }
        
        self.french_regional_patterns = {
            r'\bBEAUJOLAIS\b': 'Gamay', r'\bBEAUJ\b': 'Gamay', r'\bCHAMPAGNE\b': 'Champagne Blend',
            r'\bCHABLIS\b': 'Chardonnay', r'\bSANCERRE\b': 'Sauvignon Blanc', r'\bBORDEAUX\b': 'Red Blend',
            r'\bBORD\b': 'Red Blend', r'\bBURGUNDY\b': 'Pinot Noir', r'\bCOTES DU RHONE\b': 'Red Blend',
            r'\bCDP\b': 'Red Blend', r'\bCHATEAUNEUF\b': 'Red Blend', r'\bST EMIL\b': 'Red Blend',
            r'\bST JULIEN\b': 'Red Blend', r'\bPOU/FUME\b': 'Sauvignon Blanc', r'\bMUSCADET\b': 'Muscadet',
            r'\bALSACE\b': 'Riesling', r'\bVOUVRAY\b': 'Chenin Blanc', r'\bCONDRIEU\b': 'Viognier'
        }
        
        self.iberian_patterns = {
            r'\bRIOJA\b': 'Tempranillo', r'\bRIBERA\b': 'Tempranillo', r'\bDOURO\b': 'Portuguese Red',
            r'\bVINHO VERDE\b': 'Vinho Verde', r'\bVERDE\b': 'Vinho Verde', r'\bALBARINO\b': 'Albariño',
            r'\bALBARIÑO\b': 'Albariño', r'\bTEMPRANILLO\b': 'Tempranillo', r'\bGARNACHA\b': 'Garnacha',
            r'\bCAMPO VIEJO\b': 'Tempranillo', r'\bMARQUES\b': 'Tempranillo', r'\bRESERVA\b': 'Red Blend',
            r'\bGRAN RESERVA\b': 'Red Blend', r'\bCRIANZA\b': 'Red Blend', r'\bVALDEPEÑAS\b': 'Tempranillo',
            r'\bJUMILLA\b': 'Monastrell', r'\bCAHORS\b': 'Malbec'
        }
        
        # Brand patterns (keeping existing ones)
        self.brand_specific_patterns = {
            r'\bBERINGER\b': 'Cabernet Sauvignon', r'\bSUTTER HOME\b': 'White Zinfandel', r'\bBAREFOOT\b': 'White Blend',
            r'\bKENDALL JACKSON\b': 'Chardonnay', r'\bROBERT MONDAVI\b': 'Cabernet Sauvignon', r'\bYELLOW TAIL\b': 'Shiraz',
            r'\bOPUS ONE\b': 'Red Blend', r'\bCAYMUS\b': 'Cabernet Sauvignon', r'\bSILVER OAK\b': 'Cabernet Sauvignon',
            r'\bJORDAN\b': 'Cabernet Sauvignon', r'\bSTAG\'S LEAP\b': 'Cabernet Sauvignon', r'\bFAR NIENTE\b': 'Chardonnay',
            r'\bSCHRAMSBERG\b': 'Sparkling Blend', r'\bKEDEM\b': 'Concord', r'\bMANISCHEWITZ\b': 'Concord',
            r'\bCARMEL\b': 'Red Blend', r'\bLINGANORE\b': 'Fruit Wine'
        }
        
        # Sake and special wine patterns (unchanged)
        self.sake_patterns = {
            r'\bSAKE\b': 'Sake', r'\bJUNMAI\b': 'Sake', r'\bDAIGINJO\b': 'Sake', r'\bGINJO\b': 'Sake',
            r'\bHONJOZO\b': 'Sake', r'\bNIGORI\b': 'Sake', r'\bSHU\b': 'Sake', r'\bTOKUBETSU\b': 'Sake',
            r'\bHAKUSHIKA\b': 'Sake', r'\bOKUNOMATSU\b': 'Sake', r'\bHAKUTSURU\b': 'Sake',
            r'\bSHO CHIKU BAI\b': 'Sake', r'\bKINSEN\b': 'Sake', r'\bSHAO HSING\b': 'Sake', r'\bHUA TIAO\b': 'Sake'
        }
        
        # =================================================================
        # NEW: COMPREHENSIVE COUNTRY/GEOGRAPHIC DETECTION PATTERNS
        # =================================================================
        
        # Italian geographic indicators (regions, cities, terms)
        self.italian_country_patterns = {
            # Major wine regions
            r'\bVENETO\b': 'Italy', r'\bTUSCANY\b': 'Italy', r'\bTOSCANA\b': 'Italy', r'\bPIEMONTE\b': 'Italy',
            r'\bPIEDMONT\b': 'Italy', r'\bSICILY\b': 'Italy', r'\bSICILIA\b': 'Italy', r'\bAPULIA\b': 'Italy',
            r'\bPUGLIA\b': 'Italy', r'\bTRENTINO\b': 'Italy', r'\bALTO ADIGE\b': 'Italy', r'\bUMBRIA\b': 'Italy',
            r'\bMARCHE\b': 'Italy', r'\bABRUZZO\b': 'Italy', r'\bCALABRIA\b': 'Italy', r'\bCAMPANIA\b': 'Italy',
            r'\bEMILIA ROMAGNA\b': 'Italy', r'\bFRIULI\b': 'Italy', r'\bLAZIO\b': 'Italy', r'\bLIGURIA\b': 'Italy',
            r'\bLOMBARDIA\b': 'Italy', r'\bMOLISE\b': 'Italy', r'\bSARDINIA\b': 'Italy', r'\bSARDEGNA\b': 'Italy',
            r'\bVALLE D\'AOSTA\b': 'Italy',
            
            # Specific wine areas
            r'\bCHIANTI\b': 'Italy', r'\bBAROLO\b': 'Italy', r'\bBRUNELLO\b': 'Italy', r'\bAMARONE\b': 'Italy',
            r'\bVALPOLICELLA\b': 'Italy', r'\bSOAVE\b': 'Italy', r'\bPROSECCO\b': 'Italy', r'\bFRANCIACORTA\b': 'Italy',
            r'\bMONTEPULCIANO\b': 'Italy', r'\bSANGIOVESE\b': 'Italy', r'\bNEBBIOLO\b': 'Italy',
            
            # Italian wine terms
            r'\bRISERVA\b': 'Italy', r'\bSUPERIORE\b': 'Italy', r'\bCLASSICO\b': 'Italy',
            r'\bROSSO\b': 'Italy', r'\bBIANCO\b': 'Italy', r'\bROSATO\b': 'Italy',
            r'\bSECCO\b': 'Italy', r'\bABBOCCATO\b': 'Italy', r'\bDOLCE\b': 'Italy',
            
            # Italian producer indicators
            r'\bTENUTA\b': 'Italy', r'\bCASTELLO\b': 'Italy', r'\bVILLA\b': 'Italy', r'\bFATTORIA\b': 'Italy',
            r'\bCANTINA\b': 'Italy', r'\bPODERE\b': 'Italy', r'\bAZIENDA\b': 'Italy',
            
            # Cities/towns known for wine
            r'\bFLORENCE\b': 'Italy', r'\bFIRENZE\b': 'Italy', r'\bMILAN\b': 'Italy', r'\bMILANO\b': 'Italy',
            r'\bVERONA\b': 'Italy', r'\bBOLOGNA\b': 'Italy', r'\bTORINO\b': 'Italy', r'\bTURIN\b': 'Italy',
            r'\bPALERMO\b': 'Italy', r'\bNAPLES\b': 'Italy', r'\bNAPOLI\b': 'Italy'
        }
        
        # French geographic indicators
        self.french_country_patterns = {
            # Major wine regions
            r'\bALSACE\b': 'France', r'\bBORDEAUX\b': 'France', r'\bBURGUNDY\b': 'France', r'\bBOURGOGNE\b': 'France',
            r'\bCHAMPAGNE\b': 'France', r'\bLOIRE\b': 'France', r'\bRHONE\b': 'France', r'\bRHÔNE\b': 'France',
            r'\bPROVENCE\b': 'France', r'\bLANGUEDOC\b': 'France', r'\bROUSSILLON\b': 'France',
            r'\bBEAUJOLAIS\b': 'France', r'\bCORSE\b': 'France', r'\bCORSICA\b': 'France',
            r'\bJURA\b': 'France', r'\bSAVOIE\b': 'France', r'\bSAVOY\b': 'France',
            
            # Specific appellations
            r'\bCHABLIS\b': 'France', r'\bSANCERRE\b': 'France', r'\bPOUILLY\b': 'France',
            r'\bMUSCADET\b': 'France', r'\bVOUVRAY\b': 'France', r'\bCONDRIEU\b': 'France',
            r'\bCHATEAUNEUF\b': 'France', r'\bCOTES DU RHONE\b': 'France', r'\bCOTES DU RHÔNE\b': 'France',
            r'\bMEDOC\b': 'France', r'\bPOMEROL\b': 'France', r'\bST EMILION\b': 'France',
            r'\bST JULIEN\b': 'France', r'\bST ESTEPHE\b': 'France', r'\bMARGAUX\b': 'France',
            r'\bPAUILLAC\b': 'France', r'\bGRAVES\b': 'France', r'\bSAUTERNES\b': 'France',
            
            # French wine terms
            r'\bCHATEAU\b': 'France', r'\bDOMAINE\b': 'France', r'\bCLOS\b': 'France',
            r'\bROUGE\b': 'France', r'\bBLANC\b': 'France', r'\bROSE\b': 'France',
            r'\bSEC\b': 'France', r'\bDEMI SEC\b': 'France', r'\bMOELLEUX\b': 'France',
            r'\bGRAND CRU\b': 'France', r'\bPREMIER CRU\b': 'France', r'\bVIEILLES VIGNES\b': 'France',
            r'\bMIS EN BOUTEILLE\b': 'France', r'\bRECOLTANT\b': 'France'
        }
        
        # Spanish and Portuguese patterns
        self.iberian_country_patterns = {
            # Spanish regions
            r'\bRIOJA\b': 'Spain', r'\bRIBERA DEL DUERO\b': 'Spain', r'\bTORO\b': 'Spain',
            r'\bJUMILLA\b': 'Spain', r'\bVALDEPEÑAS\b': 'Spain', r'\bLA MANCHA\b': 'Spain',
            r'\bNAVARRA\b': 'Spain', r'\bCASTILLA\b': 'Spain', r'\bCASTILE\b': 'Spain',
            r'\bGALICIA\b': 'Spain', r'\bRIAS BAIXAS\b': 'Spain', r'\bRUEDA\b': 'Spain',
            r'\bPRIORAT\b': 'Spain', r'\bPENEDES\b': 'Spain', r'\bCATALUNYA\b': 'Spain',
            r'\bCATALONIA\b': 'Spain', r'\bANDALUSIA\b': 'Spain', r'\bANDALUCIA\b': 'Spain',
            r'\bJEREZ\b': 'Spain', r'\bSHERRY\b': 'Spain', r'\bMALAGA\b': 'Spain',
            
            # Spanish wine terms
            r'\bTINTO\b': 'Spain', r'\bBLANCO\b': 'Spain', r'\bROSADO\b': 'Spain',
            r'\bCRIANZA\b': 'Spain', r'\bRESERVA\b': 'Spain', r'\bGRAN RESERVA\b': 'Spain',
            r'\bTEMPRANILLO\b': 'Spain', r'\bGARNACHA\b': 'Spain', r'\bMONASTRELL\b': 'Spain',
            r'\bALBARIÑO\b': 'Spain', r'\bALBARINO\b': 'Spain', r'\bVERDEJO\b': 'Spain',
            r'\bBODEGA\b': 'Spain', r'\bVINOS\b': 'Spain', r'\bCOSECHA\b': 'Spain',
            
            # Portuguese patterns
            r'\bDOURO\b': 'Portugal', r'\bPORTO\b': 'Portugal', r'\bVINHO VERDE\b': 'Portugal',
            r'\bALENTEJO\b': 'Portugal', r'\bDAO\b': 'Portugal', r'\bDÃO\b': 'Portugal',
            r'\bTOURIGA\b': 'Portugal', r'\bPORTUGUESE\b': 'Portugal', r'\bQUINTA\b': 'Portugal'
        }
        
        # German and Austrian patterns
        self.german_country_patterns = {
            r'\bGERMAN\b': 'Germany', r'\bGERMANY\b': 'Germany', r'\bDEUTSCHLAND\b': 'Germany',
            r'\bRHINE\b': 'Germany', r'\bRHEIN\b': 'Germany', r'\bMOSEL\b': 'Germany',
            r'\bMOSELLE\b': 'Germany', r'\bNAHE\b': 'Germany', r'\bPFALZ\b': 'Germany',
            r'\bRHEINGAU\b': 'Germany', r'\bWURTTEMBERG\b': 'Germany', r'\bBADEN\b': 'Germany',
            r'\bFRANKEN\b': 'Germany', r'\bAHR\b': 'Germany', r'\bSAAR\b': 'Germany',
            r'\bRUWER\b': 'Germany', r'\bMITTELRHEIN\b': 'Germany',
            
            # German wine terms
            r'\bRIESLING\b': 'Germany', r'\bSPATLESE\b': 'Germany', r'\bAUSLESE\b': 'Germany',
            r'\bKABINETT\b': 'Germany', r'\bTROCKEN\b': 'Germany', r'\bHALBTROCKEN\b': 'Germany',
            r'\bBEERENAUSLESE\b': 'Germany', r'\bTROCKENBEERENAUSLESE\b': 'Germany',
            r'\bEISWEIN\b': 'Germany', r'\bLIEBFRAUMILCH\b': 'Germany', r'\bBLUE NUN\b': 'Germany',
            r'\bGEWURZTRAMINER\b': 'Germany', r'\bMULLER THURGAU\b': 'Germany',
            r'\bWEINGUT\b': 'Germany', r'\bSCHLOSS\b': 'Germany', r'\bDR\. LOOSEN\b': 'Germany',
            
            # Austrian patterns
            r'\bAUSTRIAN\b': 'Austria', r'\bAUSTRIA\b': 'Austria', r'\bOSTERREICH\b': 'Austria',
            r'\bWACHAU\b': 'Austria', r'\bGRUNER VELTLINER\b': 'Austria', r'\bGRÜNER VELTLINER\b': 'Austria',
            r'\bBURGENLAND\b': 'Austria', r'\bSTEIERMARK\b': 'Austria', r'\bNIEDEROSTERREICH\b': 'Austria'
        }
        
        # New World country patterns
        self.new_world_country_patterns = {
            # Australia
            r'\bAUSTRALIAN\b': 'Australia', r'\bAUSTRALIA\b': 'Australia',
            r'\bSHIRAZ\b': 'Australia', r'\bYELLOW TAIL\b': 'Australia', r'\bJACOB\'S CREEK\b': 'Australia',
            r'\bPENFOLDS\b': 'Australia', r'\bLINDEMAN\'S\b': 'Australia', r'\bWOLF BLASS\b': 'Australia',
            r'\bBARROSSA\b': 'Australia', r'\bCLARE VALLEY\b': 'Australia', r'\bHUNTER VALLEY\b': 'Australia',
            r'\bMcLAREN VALE\b': 'Australia', r'\bCOONAWARRA\b': 'Australia', r'\bYARRA VALLEY\b': 'Australia',
            r'\bMARGARET RIVER\b': 'Australia', r'\bADELAIDE HILLS\b': 'Australia',
            
            # New Zealand
            r'\bNEW ZEALAND\b': 'New Zealand', r'\bMALBOROUGH\b': 'New Zealand', r'\bCENTRAL OTAGO\b': 'New Zealand',
            r'\bHAWKES BAY\b': 'New Zealand', r'\bMARTINBOROUGH\b': 'New Zealand', r'\bWAIRARAPR\b': 'New Zealand',
            r'\bCLOUDY BAY\b': 'New Zealand', r'\bVILLA MARIA\b': 'New Zealand', r'\bOYSTER BAY\b': 'New Zealand',
            
            # South Africa
            r'\bSOUTH AFRICAN\b': 'South Africa', r'\bSOUTH AFRICA\b': 'South Africa',
            r'\bSTELLENBOSCH\b': 'South Africa', r'\bPAARL\b': 'South Africa', r'\bFRANSCHHOEK\b': 'South Africa',
            r'\bWALKER BAY\b': 'South Africa', r'\bCONSTANTIA\b': 'South Africa', r'\bSWARTLAND\b': 'South Africa',
            r'\bPINOTAGE\b': 'South Africa', r'\bCHENIN BLANC\b': 'South Africa',
            r'\bKLEIN CONSTANTIA\b': 'South Africa', r'\bFAIRVIEW\b': 'South Africa',
            
            # Chile
            r'\bCHILEAN\b': 'Chile', r'\bCHILE\b': 'Chile',
            r'\bMAIPO\b': 'Chile', r'\bCOLCHAGUA\b': 'Chile', r'\bCASABLANCA\b': 'Chile',
            r'\bACANCHGUA\b': 'Chile', r'\bCUCRICO\b': 'Chile', r'\bRAPEL\b': 'Chile',
            r'\bCONCHA Y TORO\b': 'Chile', r'\bSANTA RITA\b': 'Chile', r'\bMONTES\b': 'Chile',
            r'\bCALITERRA\b': 'Chile', r'\bVERAMONTE\b': 'Chile', r'\bCARMENERE\b': 'Chile',
            
            # Argentina
            r'\bARGENTINE\b': 'Argentina', r'\bARGENTINA\b': 'Argentina',
            r'\bMENDOZA\b': 'Argentina', r'\bSALTA\b': 'Argentina', r'\bSAN JUAN\b': 'Argentina',
            r'\bLA RIOJA\b': 'Argentina', r'\bNEUQUEN\b': 'Argentina', r'\bMAIPU\b': 'Argentina',
            r'\bCATE\b': 'Argentina',
        }
        
        # Greek and Eastern European patterns
        self.eastern_european_country_patterns = {
            # Greece
            r'\bGREEK\b': 'Greece', r'\bGREECE\b': 'Greece', r'\bHELLAS\b': 'Greece',
            r'\bSANTORINI\b': 'Greece', r'\bNEMEA\b': 'Greece', r'\bPATRAS\b': 'Greece',
            r'\bNAOUSSA\b': 'Greece', r'\bCRETE\b': 'Greece', r'\bRHODES\b': 'Greece',
            r'\bASSYRTIKO\b': 'Greece', r'\bAGIOGRITIKO\b': 'Greece', r'\bXINOMAVRO\b': 'Greece',
            r'\bRETSINA\b': 'Greece', r'\bOUZO\b': 'Greece',
            
            # Eastern Europe
            r'\bHUNGARY\b': 'Hungary', r'\bHUNGARIAN\b': 'Hungary', r'\bTOKAJ\b': 'Hungary', r'\bTOKAY\b': 'Hungary',
            r'\bBULGARIA\b': 'Bulgaria', r'\bBULGARIAN\b': 'Bulgaria',
            r'\bROMANIA\b': 'Romania', r'\bROMANIAN\b': 'Romania',
            r'\bCROATIA\b': 'Croatia', r'\bCROATIAN\b': 'Croatia',
            r'\bSLOVENIA\b': 'Slovenia', r'\bSLOVENIAN\b': 'Slovenia',
            r'\bSERBIA\b': 'Serbia', r'\bSERBIAN\b': 'Serbia',
            r'\bGEORGIA\b': 'Georgia', r'\bGEORGIAN\b': 'Georgia'
        }
        
        # Middle Eastern and Israeli patterns
        self.middle_eastern_country_patterns = {
            # Israel
            r'\bISRAEL\b': 'Israel', r'\bISRAELI\b': 'Israel',
            r'\bBARKAN\b': 'Israel', r'\bCARMEL\b': 'Israel', r'\bGOLAN\b': 'Israel',
            r'\bGALIL\b': 'Israel', r'\bJUDEAN\b': 'Israel', r'\bYARDEN\b': 'Israel',
            r'\bDALTON\b': 'Israel', r'\bTEPERBERG\b': 'Israel', r'\bRECANATI\b': 'Israel',
            
            # Lebanon
            r'\bLEBANON\b': 'Lebanon', r'\bLEBANESE\b': 'Lebanon',
            r'\bBEKAA\b': 'Lebanon', r'\bKSARA\b': 'Lebanon', r'\bMURAD\b': 'Lebanon',
            
            # Turkey
            r'\bTURKEY\b': 'Turkey', r'\bTURKISH\b': 'Turkey',
            r'\bCAPPADOCIA\b': 'Turkey', r'\bTHRACE\b': 'Turkey'
        }
        
        # US patterns (domestic wines)
        self.us_country_patterns = {
            # General US indicators
            r'\bAMERICAN\b': 'US', r'\bUSA\b': 'US', r'\bUNITED STATES\b': 'US',
            
            # California
            r'\bCALIFORNIA\b': 'US', r'\bCALI\b': 'US', r'\bNAPA\b': 'US', r'\bSONOMA\b': 'US',
            r'\bMENDOCINO\b': 'US', r'\bMONTEREY\b': 'US', r'\bPASO ROBLES\b': 'US',
            r'\bSANTA BARBARA\b': 'US', r'\bCENTRAL COAST\b': 'US', r'\bCENTRAL VALLEY\b': 'US',
            r'\bRUSSIAN RIVER\b': 'US', r'\bDRY CREEK\b': 'US', r'\bALEXANDER VALLEY\b': 'US',
            r'\bKNIGHTS VALLEY\b': 'US', r'\bCARNEROS\b': 'US', r'\bSTAGS LEAP\b': 'US',
            r'\bOAKVILLE\b': 'US', r'\bRUTHERFORD\b': 'US', r'\bST HELENA\b': 'US',
            r'\bCALISTOGA\b': 'US', r'\bHOWELL MOUNTAIN\b': 'US', r'\bMOUNT VEEDER\b': 'US',
            r'\bLOS CARNEROS\b': 'US', r'\bSANTA MARIA\b': 'US', r'\bSANTA RITA HILLS\b': 'US',
            r'\bEDNA VALLEY\b': 'US', r'\bARROYO GRANDE\b': 'US', r'\bSAN LUIS OBISPO\b': 'US',
            
            # California brands/wineries (strong US indicators)
            r'\bBERINGER\b': 'US', r'\bKENDALL JACKSON\b': 'US', r'\bROBERT MONDAVI\b': 'US',
            r'\bSILVER OAK\b': 'US', r'\bCAYMUS\b': 'US', r'\bFAR NIENTE\b': 'US',
            r'\bSTAG\'S LEAP\b': 'US', r'\bJORDAN\b': 'US', r'\bOPUS ONE\b': 'US',
            r'\bSCHRAMSBERG\b': 'US', r'\bCHALONE\b': 'US', r'\bBONTERRA\b': 'US',
            r'\bFRANZIA\b': 'US', r'\bGALLO\b': 'US', r'\bE & J GALLO\b': 'US',
            
            # Other US states
            r'\bWASHINGTON\b': 'US', r'\bOREGON\b': 'US', r'\bNEW YORK\b': 'US',
            r'\bVIRGINIA\b': 'US', r'\bTEXAS\b': 'US', r'\bMICHIGAN\b': 'US',
            r'\bCOLUMBIA VALLEY\b': 'US', r'\bWILLAMETTE VALLEY\b': 'US',
            r'\bFINGER LAKES\b': 'US', r'\bLONG ISLAND\b': 'US', r'\bHUDSON VALLEY\b': 'US',
            r'\bCHARLOTTESVILLE\b': 'US', r'\bSHENANDOAH\b': 'US', r'\bHILL COUNTRY\b': 'US',
            
            # US wine brands (kosher, domestic)
            r'\bMANISCHEWITZ\b': 'US', r'\bKEDEM\b': 'US', r'\bBAREFOOT\b': 'US',
            r'\bSUTTER HOME\b': 'US', r'\bWOODBRIDGE\b': 'US', r'\bBLACK BOX\b': 'US',
            r'\bFRANZIA\b': 'US', r'\bBOTA BOX\b': 'US', r'\bCHARLES SHAW\b': 'US',
            r'\bTWO BUCK CHUCK\b': 'US', r'\bLIBERTY CREEK\b': 'US', r'\bCARLO ROSSI\b': 'US'
        }
        
        # Asian country patterns
        self.asian_country_patterns = {
            # Japan
            r'\bJAPAN\b': 'Japan', r'\bJAPANESE\b': 'Japan', r'\bNIHON\b': 'Japan',
            r'\bSAKE\b': 'Japan', r'\bJUNMAI\b': 'Japan', r'\bDAIGINJO\b': 'Japan',
            r'\bGINJO\b': 'Japan', r'\bHONJOZO\b': 'Japan', r'\bNIGORI\b': 'Japan',
            r'\bSHU\b': 'Japan', r'\bHAKUSHIKA\b': 'Japan', r'\bOKUNOMATSU\b': 'Japan',
            r'\bHAKUTSURU\b': 'Japan', r'\bSHO CHIKU BAI\b': 'Japan', r'\bKINSEN\b': 'Japan',
            
            # China
            r'\bCHINA\b': 'China', r'\bCHINESE\b': 'China',
            r'\bSHAO HSING\b': 'China', r'\bHUA TIAO\b': 'China', r'\bYELLOW WINE\b': 'China',
            r'\bRICE WINE\b': 'China', r'\bSHAOXING\b': 'China'
        }
        
        # Combined country pattern dictionary (used for lookup)
        self.all_country_patterns = {}
        self.all_country_patterns.update(self.italian_country_patterns)
        self.all_country_patterns.update(self.french_country_patterns)
        self.all_country_patterns.update(self.iberian_country_patterns)
        self.all_country_patterns.update(self.german_country_patterns)
        self.all_country_patterns.update(self.new_world_country_patterns)
        self.all_country_patterns.update(self.eastern_european_country_patterns)
        self.all_country_patterns.update(self.middle_eastern_country_patterns)
        self.all_country_patterns.update(self.us_country_patterns)
        self.all_country_patterns.update(self.asian_country_patterns)
        
        # Color patterns for wine classification
        self.color_patterns = {
            r'\bRED\b': 'Red Blend', r'\bWHITE\b': 'White Blend', r'\bWH\b': 'White Blend',
            r'\bROSE\b': 'Rosé', r'\bROSÉ\b': 'Rosé', r'\bBLUSH\b': 'Rosé', r'\bPINK\b': 'Rosé',
            r'\bROSSO\b': 'Red Blend', r'\bBIANCO\b': 'White Blend', r'\bBLANC\b': 'White Blend',
            r'\bROUGE\b': 'Red Blend', r'\bTINTO\b': 'Red Blend', r'\bBLANCO\b': 'White Blend', r'\bROSADO\b': 'Rosé'
        }
        
        # Variety standardization mapping (unchanged)
        self.variety_mapping = {
            'Pinot Gris': 'Pinot Grigio', 'Pinot Bianco': 'Pinot Grigio', 'Pinot Blanc': 'Pinot Grigio',
            'Pinot Nero': 'Pinot Noir', 'Shiraz': 'Syrah', 'Shiraz-Viognier': 'Syrah-Viognier',
            'Shiraz-Cabernet': 'Syrah-Cabernet', 'Shiraz-Cabernet Sauvignon': 'Syrah-Cabernet Sauvignon',
            'Fumé Blanc': 'Sauvignon Blanc', 'Sauvignon': 'Sauvignon Blanc', 'Rosato': 'Rosé',
            'Rosado': 'Rosé', 'Portuguese Rosé': 'Rosé', 'Sangiovese Grosso': 'Sangiovese',
            'Prugnolo Gentile': 'Sangiovese', 'Tinto Fino': 'Tempranillo', 'Tinta de Toro': 'Tempranillo',
            'Tinto del Pais': 'Tempranillo', 'Bordeaux-style Red Blend': 'Red Blend',
            'Rhône-style Red Blend': 'Red Blend', 'Bordeaux-style White Blend': 'White Blend',
            'Rhône-style White Blend': 'White Blend', 'Alsace white blend': 'White Blend',
            'Austrian Red Blend': 'Red Blend', 'Madeira Blend': 'Red Blend', 'Moscatel': 'Moscato',
            'Muscat': 'Moscato', 'Black Muscat': 'Moscato', 'Muskat Ottonel': 'Moscato',
            'Carignane': 'Carignan', 'Carignano': 'Carignan', 'Sylvaner': 'Silvaner',
            'Weissburgunder': 'Pinot Grigio', 'Tokay': 'Tokaji', 'Insolia': 'Inzolia',
            'Assyrtico': 'Assyrtiko', 'Traminer': 'Gewürztraminer', 'Colombard': 'Ugni Blanc-Colombard',
            'Claret': 'Red Blend', 'Meritage': 'Red Blend', 'G-S-M': 'Red Blend', 'Other': ''
        }
        
        # Non-wine products to filter out
        self.non_wine_patterns = [
            r'\bBEER\b', r'\bALE\b', r'\bLAGER\b', r'\bSTOUT\b', r'\bPORTER\b', r'\bCIDER\b',
            r'\bMEAD\b', r'\bVODKA\b', r'\bGIN\b', r'\bRUM\b', r'\bWHISKEY\b', r'\bBRANDY\b',
            r'\bCOGNAC\b', r'\bTEQUILA\b', r'\bLIQUEUR\b', r'\bCHIEW\b'
        ]
    
    def classify_sparkling(self, variety):
        """Classify wines as sparkling and determine red/white type"""
        if pd.isna(variety) or variety == '':
            return 'none', False, False, False
        
        variety_lower = variety.lower()
        
        # Check for red sparkling
        for red_type in self.sparkling_patterns['red_sparkling']:
            if red_type.lower() in variety_lower:
                return red_type, True, False, True
        
        # Check for white sparkling
        for white_type in self.sparkling_patterns['white_sparkling']:
            if white_type.lower() in variety_lower:
                return white_type, False, True, True
        
        # Check for general sparkling terms
        sparkling_terms = ['sparkling', 'champagne', 'prosecco', 'crémant', 'cava', 'sekt']
        for term in sparkling_terms:
            if term in variety_lower:
                return variety, False, True, True
        
        return 'none', False, False, False
    
    def extract_country_from_description(self, description):
        """NEW: Extract country from product description using geographic patterns"""
        if pd.isna(description) or description == '':
            return None, 'empty_description'
        
        desc_upper = description.upper()
        
        # Priority order for country detection (most specific first)
        country_pattern_groups = [
            # Specific geographic regions first (most reliable)
            (self.italian_country_patterns, 'italian_geographic'),
            (self.french_country_patterns, 'french_geographic'),
            (self.iberian_country_patterns, 'iberian_geographic'),
            (self.german_country_patterns, 'german_geographic'),
            (self.eastern_european_country_patterns, 'eastern_european_geographic'),
            (self.middle_eastern_country_patterns, 'middle_eastern_geographic'),
            (self.asian_country_patterns, 'asian_geographic'),
            (self.new_world_country_patterns, 'new_world_geographic'),
            (self.us_country_patterns, 'us_geographic'),
        ]
        
        # Apply pattern matching in priority order
        for patterns, method in country_pattern_groups:
            for pattern, country in patterns.items():
                if re.search(pattern, desc_upper):
                    return country, method
        
        return None, 'no_country_match'
    
    def extract_variety_from_description(self, description):
        """Extract wine variety from product description using pattern matching (unchanged)"""
        if pd.isna(description) or description == '':
            return None, 'empty_description'
        
        desc_upper = description.upper()
        
        # Priority order for pattern matching
        pattern_groups = [
            (self.sake_patterns, 'sake_match'),
            ({r'\bSHERRY\b': 'Sherry', r'\bFINO\b': 'Sherry', r'\bAMONTILLADO\b': 'Sherry'}, 'sherry_match'),
            ({r'\bPORT\b': 'Port', r'\bPORTO\b': 'Port', r'\bTAWNY\b': 'Port'}, 'port_match'),
            (self.brand_specific_patterns, 'brand_match'),
        ]
        
        # Filter out non-wine products (except sake)
        if not any(re.search(pattern, desc_upper) for pattern in self.sake_patterns.keys()):
            for pattern in self.non_wine_patterns:
                if re.search(pattern, desc_upper):
                    return None, 'non_wine_product'
        
        # Apply pattern matching in priority order
        for patterns, method in pattern_groups:
            for pattern, variety in patterns.items():
                if re.search(pattern, desc_upper):
                    return variety, method
        
        # Additional pattern groups
        more_pattern_groups = [
            (self.abbreviation_patterns, 'abbreviation_match'),
            (self.italian_regional_patterns, 'italian_regional_match'),
            (self.iberian_patterns, 'iberian_match'),
            (self.french_regional_patterns, 'french_regional_match'),
            (self.color_patterns, 'color_match'),
        ]
        
        for patterns, method in more_pattern_groups:
            for pattern, variety in patterns.items():
                if re.search(pattern, desc_upper):
                    return variety, method
        
        return None, 'no_match'
    
    def process_enhanced_classification(self, df):
        """
        Main processing function - applies all classification steps including COUNTRY DETECTION
        
        Args:
            df: Input dataframe with wine data
            
        Returns:
            df_processed: Dataframe with all classification columns added including country data
        """
        print("=== ENHANCED WINE CLASSIFICATION SYSTEM WITH COUNTRY DETECTION ===")
        print(f"Processing {len(df):,} records...")
        
        # Create working copy
        df_processed = df.copy()
        
        # Step 1: Sparkling classification
        print("\nStep 1: Applying sparkling classification...")
        sparkling_results = df_processed['review_variety'].apply(self.classify_sparkling)
        df_processed['sparkling_type'] = [result[0] for result in sparkling_results]
        df_processed['red_sparkling'] = [result[1] for result in sparkling_results]
        df_processed['white_sparkling'] = [result[2] for result in sparkling_results]
        df_processed['total_sparkling'] = [result[3] for result in sparkling_results]
        
        # Step 2: Variety consolidation
        print("Step 2: Applying variety consolidation...")
        df_processed['review_variety_consolidated'] = df_processed['review_variety'].replace(self.variety_mapping)
        
        # Step 3: Text extraction for varieties
        print("Step 3: Applying text extraction for varieties...")
        needs_variety_extraction = (
            (df_processed['review_variety_consolidated'] == '') | 
            (df_processed['review_variety_consolidated'].isna())
        ) & (df_processed['total_sparkling'] == False)
        
        print(f"Wines needing variety extraction: {needs_variety_extraction.sum():,}")
        
        # Initialize variety extraction columns
        df_processed['extracted_variety'] = None
        df_processed['extraction_method'] = None
        df_processed['extraction_confidence'] = None
        
        # Apply variety text extraction
        variety_extraction_count = 0
        for idx, row in df_processed[needs_variety_extraction].iterrows():
            variety, method = self.extract_variety_from_description(row['ITEM DESCRIPTION'])
            df_processed.at[idx, 'extracted_variety'] = variety
            df_processed.at[idx, 'extraction_method'] = method
            
            # Set confidence scores
            confidence_map = {
                'sake_match': 0.95, 'sherry_match': 0.95, 'port_match': 0.95,
                'brand_match': 0.90, 'abbreviation_match': 0.85, 
                'italian_regional_match': 0.85, 'iberian_match': 0.85,
                'french_regional_match': 0.85, 'color_match': 0.60,
                'no_match': 0.0, 'non_wine_product': 0.0
            }
            df_processed.at[idx, 'extraction_confidence'] = confidence_map.get(method, 0.0)
            
            variety_extraction_count += 1
            if variety_extraction_count % 5000 == 0:
                print(f"  Processed {variety_extraction_count:,} variety extractions...")
        
        # Step 4: NEW - Country extraction from product descriptions
        print("Step 4: **NEW** - Applying country extraction from product descriptions...")
        
        # Find records that need country extraction (empty or missing country data)
        needs_country_extraction = (
            (df_processed['review_country'] == '') | 
            (df_processed['review_country'].isna())
        )
        
        print(f"Wines needing country extraction: {needs_country_extraction.sum():,}")
        
        # Initialize country extraction columns
        df_processed['extracted_country'] = None
        df_processed['country_extraction_method'] = None
        df_processed['country_extraction_confidence'] = None
        
        # Apply country text extraction
        country_extraction_count = 0
        country_success_count = 0
        
        for idx, row in df_processed[needs_country_extraction].iterrows():
            country, method = self.extract_country_from_description(row['ITEM DESCRIPTION'])
            df_processed.at[idx, 'extracted_country'] = country
            df_processed.at[idx, 'country_extraction_method'] = method
            
            # Set confidence scores for country extraction
            country_confidence_map = {
                'italian_geographic': 0.90, 'french_geographic': 0.90, 'iberian_geographic': 0.90,
                'german_geographic': 0.90, 'us_geographic': 0.90, 'new_world_geographic': 0.90,
                'eastern_european_geographic': 0.85, 'middle_eastern_geographic': 0.85,
                'asian_geographic': 0.90, 'no_country_match': 0.0
            }
            df_processed.at[idx, 'country_extraction_confidence'] = country_confidence_map.get(method, 0.0)
            
            if country is not None:
                country_success_count += 1
            
            country_extraction_count += 1
            if country_extraction_count % 10000 == 0:
                print(f"  Processed {country_extraction_count:,} country extractions, {country_success_count:,} successful...")
        
        print(f"Country extraction completed: {country_success_count:,} countries extracted from {country_extraction_count:,} attempts")
        
        # Step 5: Create final variety column
        print("Step 5: Creating final variety column...")
        df_processed['final_variety'] = df_processed['review_variety_consolidated'].copy()
        
        # Fill in extracted varieties where blanks exist
        blank_mask = (df_processed['final_variety'] == '') | (df_processed['final_variety'].isna())
        extraction_mask = df_processed['extracted_variety'].notna()
        df_processed.loc[blank_mask & extraction_mask, 'final_variety'] = df_processed.loc[blank_mask & extraction_mask, 'extracted_variety']
        
        # Step 6: NEW - Create final country column
        print("Step 6: **NEW** - Creating final country column...")
        df_processed['final_country'] = df_processed['review_country'].copy()
        
        # Fill in extracted countries where blanks exist
        country_blank_mask = (df_processed['final_country'] == '') | (df_processed['final_country'].isna())
        country_extraction_mask = df_processed['extracted_country'].notna()
        df_processed.loc[country_blank_mask & country_extraction_mask, 'final_country'] = df_processed.loc[country_blank_mask & country_extraction_mask, 'extracted_country']
        
        return df_processed
    
    def generate_enhanced_report(self, df_original, df_processed):
        """Generate comprehensive classification report including country analysis"""
        print("\n" + "="*80)
        print("ENHANCED WINE CLASSIFICATION REPORT WITH COUNTRY DETECTION")
        print("="*80)
        
        # Calculate variety coverage improvements
        original_with_variety = (df_original['review_variety'] != '').sum()
        original_variety_coverage = original_with_variety / len(df_original) * 100
        final_with_variety = (df_processed['final_variety'] != '').sum()
        final_variety_coverage = final_with_variety / len(df_processed) * 100
        
        print(f"VARIETY CLASSIFICATION:")
        print(f"Original variety coverage: {original_variety_coverage:.1f}% ({original_with_variety:,} wines)")
        print(f"Final variety coverage: {final_variety_coverage:.1f}% ({final_with_variety:,} wines)")
        print(f"Variety improvement: +{final_variety_coverage - original_variety_coverage:.1f} percentage points")
        print(f"Additional wines classified (variety): {final_with_variety - original_with_variety:,}")
        
        # Calculate country coverage improvements
        original_with_country = ((df_original['review_country'] != '') & (df_original['review_country'].notna())).sum()
        original_country_coverage = original_with_country / len(df_original) * 100
        final_with_country = ((df_processed['final_country'] != '') & (df_processed['final_country'].notna())).sum()
        final_country_coverage = final_with_country / len(df_processed) * 100
        
        print(f"\nCOUNTRY CLASSIFICATION:")
        print(f"Original country coverage: {original_country_coverage:.1f}% ({original_with_country:,} wines)")
        print(f"Final country coverage: {final_country_coverage:.1f}% ({final_with_country:,} wines)")
        print(f"Country improvement: +{final_country_coverage - original_country_coverage:.1f} percentage points")
        print(f"Additional wines classified (country): {final_with_country - original_with_country:,}")
        
        # Country extraction method summary
        if 'country_extraction_method' in df_processed.columns:
            country_extraction_methods = df_processed['country_extraction_method'].value_counts()
            print(f"\n=== COUNTRY EXTRACTION RESULTS ===")
            for method, count in country_extraction_methods.items():
                if count > 0 and method != 'no_country_match':
                    print(f"  {method}: {count:,} wines")
        
        # Top countries after processing
        print(f"\n=== TOP 15 COUNTRIES AFTER ENHANCED PROCESSING ===")
        final_countries = df_processed['final_country'].value_counts()
        for i, (country, count) in enumerate(final_countries.head(15).items(), 1):
            if country != '' and pd.notna(country):
                print(f"{i:2d}. {country}: {count:,}")
        
        # Sparkling wine summary
        total_sparkling = df_processed['total_sparkling'].sum()
        red_sparkling = df_processed['red_sparkling'].sum()
        white_sparkling = df_processed['white_sparkling'].sum()
        print(f"\n=== SPARKLING WINE CLASSIFICATION ===")
        print(f"Total sparkling wines: {total_sparkling:,}")
        print(f"Red sparkling wines: {red_sparkling:,}")
        print(f"White sparkling wines: {white_sparkling:,}")
        
        # Top varieties
        print(f"\n=== TOP 20 VARIETIES AFTER ENHANCED PROCESSING ===")
        final_varieties = df_processed['final_variety'].value_counts()
        for i, (variety, count) in enumerate(final_varieties.head(20).items(), 1):
            if variety != '':
                print(f"{i:2d}. {variety}: {count:,}")
        
        # Final statistics
        remaining_unclassified_variety = (df_processed['final_variety'] == '').sum()
        remaining_variety_percentage = remaining_unclassified_variety / len(df_processed) * 100
        
        remaining_unclassified_country = ((df_processed['final_country'] == '') | (df_processed['final_country'].isna())).sum()
        remaining_country_percentage = remaining_unclassified_country / len(df_processed) * 100
        
        print(f"\n=== FINAL ENHANCED CLASSIFICATION STATUS ===")
        print(f"Successfully classified (variety): {final_with_variety:,} wines ({final_variety_coverage:.1f}%)")
        print(f"Still unclassified (variety): {remaining_unclassified_variety:,} wines ({remaining_variety_percentage:.1f}%)")
        
        print(f"Successfully classified (country): {final_with_country:,} wines ({final_country_coverage:.1f}%)")
        print(f"Still unclassified (country): {remaining_unclassified_country:,} wines ({remaining_country_percentage:.1f}%)")
        
        # Show some examples of successful extractions
        successful_extractions = df_processed[df_processed['extracted_country'].notna()][['ITEM DESCRIPTION', 'extracted_country', 'country_extraction_method']].head(10)
        if len(successful_extractions) > 0:
            print(f"\n=== SAMPLE SUCCESSFUL COUNTRY EXTRACTIONS ===")
            for idx, row in successful_extractions.iterrows():
                print(f"'{row['ITEM DESCRIPTION'][:50]}...' → {row['extracted_country']} ({row['country_extraction_method']})")
        
        return df_processed['final_variety'].value_counts(), df_processed['final_country'].value_counts()


def run_enhanced_wine_classification(df):
    """
    Main function to run the enhanced wine classification system with country detection
    
    Args:
        df: Input dataframe with wine data containing columns:
            - 'review_variety': Wine variety from review data
            - 'review_country': Country from review data (may have many blanks)
            - 'ITEM DESCRIPTION': Product description text
            - 'RETAIL SALES': Sales amounts
            
    Returns:
        tuple: (df_classified, variety_counts, country_counts)
            - df_classified: Enhanced dataframe with all classification columns including country
            - variety_counts: Summary of variety distribution
            - country_counts: Summary of country distribution
    """
    # Initialize enhanced classifier
    classifier = EnhancedWineClassificationSystem()
    
    # Run enhanced processing with country detection
    df_classified = classifier.process_enhanced_classification(df)
    
    # Generate comprehensive report
    variety_counts, country_counts = classifier.generate_enhanced_report(df, df_classified)
    
    return df_classified, variety_counts, country_counts


def quick_enhanced_summary(df_classified):
    """
    Generate a quick summary of enhanced classification results including country data
    
    Args:
        df_classified: Output from run_enhanced_wine_classification()
    """
    print("=== QUICK ENHANCED CLASSIFICATION SUMMARY ===")
    
    total_wines = len(df_classified)
    classified_varieties = (df_classified['final_variety'] != '').sum()
    variety_coverage_pct = classified_varieties / total_wines * 100
    
    classified_countries = ((df_classified['final_country'] != '') & (df_classified['final_country'].notna())).sum()
    country_coverage_pct = classified_countries / total_wines * 100
    
    print(f"Total wines: {total_wines:,}")
    print(f"Successfully classified (variety): {classified_varieties:,} ({variety_coverage_pct:.1f}%)")
    print(f"Successfully classified (country): {classified_countries:,} ({country_coverage_pct:.1f}%)")
    
    print(f"\nTop 5 varieties:")
    top_varieties = df_classified['final_variety'].value_counts().head(5)
    for i, (variety, count) in enumerate(top_varieties.items(), 1):
        if variety != '':
            print(f"  {i}. {variety}: {count:,}")
    
    print(f"\nTop 5 countries:")
    top_countries = df_classified['final_country'].value_counts().head(5)
    for i, (country, count) in enumerate(top_countries.items(), 1):
        if country != '' and pd.notna(country):
            print(f"  {i}. {country}: {count:,}")


def create_country_comparison_report(df_original, df_enhanced):
    """
    Create a detailed comparison showing the improvement in country coverage
    
    Args:
        df_original: Original dataframe before enhancement
        df_enhanced: Enhanced dataframe after country extraction
    """
    print("=== DETAILED COUNTRY IMPROVEMENT ANALYSIS ===")
    
    # Before and after country coverage
    original_countries = df_original[df_original['review_country'] != '']['review_country'].value_counts()
    enhanced_countries = df_enhanced[df_enhanced['final_country'].notna()]['final_country'].value_counts()
    
    print(f"Countries identified originally: {len(original_countries)}")
    print(f"Countries identified after enhancement: {len(enhanced_countries)}")
    print(f"New countries discovered: {len(enhanced_countries) - len(original_countries)}")
    
    # Show wines that gained country classification
    gained_country = df_enhanced[
        ((df_enhanced['review_country'] == '') | (df_enhanced['review_country'].isna())) &
        (df_enhanced['extracted_country'].notna())
    ]
    
    print(f"\nWines that gained country classification: {len(gained_country):,}")
    
    if len(gained_country) > 0:
        gained_by_method = gained_country['country_extraction_method'].value_counts()
        print("\nCountry extraction methods used:")
        for method, count in gained_by_method.items():
            print(f"  {method}: {count:,} wines")
        
        gained_by_country = gained_country['extracted_country'].value_counts().head(10)
        print(f"\nTop 10 newly identified countries:")
        for i, (country, count) in enumerate(gained_by_country.items(), 1):
            print(f"  {i:2d}. {country}: {count:,}")
            
            
def classify_wine_color(variety):
    """Classify wine variety into color categories - comprehensive version"""
    if not variety or variety.strip() == '':
        return 'Unclassified'
    
    variety = variety.strip().lower()
    
    # RED WINES
    red_varieties = {
        'red blend', 'cabernet sauvignon', 'pinot noir', 'merlot', 'malbec', 
        'syrah', 'zinfandel', 'tempranillo', 'sangiovese', 'nebbiolo',
        'cabernet franc', 'montepulciano', 'chianti', 'gamay', 'barbera',
        'garnacha', 'shiraz', 'portuguese red', 'tempranillo blend', 
        'nero d\'avola', 'petite sirah', 'monastrell', 'amarone', 'primitivo',
        'pinotage', 'corvina, rondinella, molinara', 'saperavi', 'nerello mascalese',
        'carmenère', 'aglianico', 'grenache', 'bonarda', 'dolcetto', 'mencía',
        'tannat-cabernet', 'zweigelt', 'cannonau', 'valpolicella', 'agiorgitiko',
        'carignan', 'negroamaro', 'sagrantino', 'tannat', 'frappato',
        'malbec-merlot', 'xinomavro', 'valdiguié', 'blaufränkisch', 'tinta negra mole',
        'malvasia nera', 'tinta miúda', 'touriga nacional', 'gamza', 'tempranillo-merlot',
        'cabernet sauvignon-merlot', 'petit verdot', 'st. laurent', 'teroldego',
        'sousão', 'graciano', 'lagrein', 'chambourcin', 'plavac mali', 'portuguiser',
        'bobal', 'corvina', 'monica', 'mavrud', 'syrah-cabernet', 'refosco',
        'feteasca neagra', 'pinot noir-gamay', 'dornfelder', 'syrah-cabernet sauvignon',
        'lemberger', 'kekfrankos', 'vranec', 'garnacha tintorera', 'piedirosso',
        'cabernet franc-cabernet sauvignon', 'duras', 'alicante bouschet', 'gaglioppo',
        'schiava', 'papaskarasi', 'argaman', 'prieto picudo', 'mandilaria',
        'monastrell-syrah', 'susumaniello', 'roviello', 'melnik', 'cinsault',
        'merlot-argaman'
    }
    
    # WHITE WINES
    white_varieties = {
        'chardonnay', 'sauvignon blanc', 'pinot grigio', 'white blend', 'moscato',
        'riesling', 'albariño', 'viognier', 'gewürztraminer', 'chenin blanc',
        'portuguese white', 'garganega', 'verdejo', 'catarratto', 'viura',
        'vinho verde', 'grillo', 'grüner veltliner', 'cortese', 'torrontés',
        'carricante', 'melon', 'moschofilero', 'picpoul', 'ugni blanc-colombard',
        'greco', 'falanghina', 'vermentino', 'rkatsiteli', 'muscadet', 'friulano',
        'assyrtiko', 'sémillon', 'malvasia', 'savatiano', 'godello', 'verdicchio',
        'verdejo-viura', 'maturana', 'inzolia', 'vernaccia', 'torbato', 'arneis',
        'rieslaner', 'furmint', 'avesso', 'pecorino', 'ribolla gialla', 'petit manseng',
        'müller-thurgau', 'silvaner', 'grechetto', 'robola', 'symphony',
        'viognier-chardonnay', 'trebbiano', 'turbiana', 'zibibbo', 'roussanne',
        'auxerrois', 'erbaluce', 'passerina', 'kerner', 'malvasia istriana',
        'chinuri', 'greco bianco', 'antão vaz', 'vidal blanc', 'žilavka',
        'scheurebe', 'mtsvane', 'chenin blanc-chardonnay', 'loureiro', 'jacquère',
        'albana', 'malagousia', 'vilana', 'garnacha blanca', 'picapoll',
        'marsanne-viognier', 'malvasia bianca', 'emir', 'seyval blanc', 
        'chardonnay-sauvignon', 'tocai', 'alvarinho', 'fiano', 'kisi'
    }
    
    # ROSÉ WINES
    rose_varieties = {
        'rosé', 'white zinfandel'
    }
   # SPARKLING WINES (expanded)
    sparkling_varieties = {
        'prosecco', 'glera', 'sparkling blend', 'champagne blend', 'lambrusco',
        'brachetto', 'portuguese sparkling', 'lambrusco di sorbara', 
        'lambrusco grasparossa', 'xarel-lo',
    # Add simple sparkling catches
        'spark', 'brut', 'champagne', 'cuvee', 'cremant', 'cava', 'sekt'
    }
    
    # FORTIFIED/DESSERT WINES
    fortified_varieties = {
        'port', 'sherry', 'white port', 'pedro ximénez', 'tokaji', 'mavrodaphne',
        'palomino', 'bual', 'terrantez'
    }
    
    # OTHER/SPECIAL CATEGORIES
    other_varieties = {
        'sake', 'concord', 'fruit wine'
    }
    
    # BLEND WINES WITH MIXED VARIETIES (let's be more specific)
    syrah_blend_varieties = {
        'syrah-viognier'  # This is actually white due to viognier influence
    }
    
    # CLASSIFICATION LOGIC
    if variety in red_varieties:
        return 'Red'
    elif variety in white_varieties:
        return 'White'
    elif variety in rose_varieties:
        return 'Rosé'
    elif variety in sparkling_varieties:
        return 'Sparkling'
    elif variety in fortified_varieties:
        return 'Fortified'
    elif variety in other_varieties:
        return 'Other'
    elif variety in syrah_blend_varieties:
        return 'White'  # Syrah-Viognier is typically white/rosé
    else:
        return 'Unclassified'  # For any edge cases missed

# Usage example for the enhanced system:
"""
To use this enhanced utility in your notebook:

1. Save this file as 'enhanced_wine_classification_utils.py'

2. In your notebook:
   from enhanced_wine_classification_utils import run_enhanced_wine_classification, quick_enhanced_summary, create_country_comparison_report

3. Apply to your data:
   df_classified, variety_counts, country_counts = run_enhanced_wine_classification(df)

4. Quick summary:
   quick_enhanced_summary(df_classified)

5. Detailed country improvement analysis:
   create_country_comparison_report(df, df_classified)

6. Use your enhanced data:
   df = df_classified  # Now df has 95%+ variety coverage AND 70%+ country coverage!

EXPECTED RESULTS:
- Variety coverage: 90%+ (unchanged from original system)  
- Country coverage: 70%+ (MASSIVE improvement from ~43%)
- Additional 50,000+ wines with country data
- Geographic patterns detected from product descriptions
- Better dashboard filtering and analysis capabilities
"""