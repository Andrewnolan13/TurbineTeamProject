from enum import Enum

class TemperatureUnit(Enum):
    CELSIUS = 'celsius'
    FAHRENHEIT = 'fahrenheit'

class WindSpeedUnit(Enum):
    KILOMETERS_PER_HOUR = 'kmh'
    METERS_PER_SECOND = 'ms'
    MILES_PER_HOUR = 'mph'
    KNOTS = 'kn'

class PrecipitationUnit(Enum):
    MILLIMETERS = 'mm'
    INCHES = 'inch'

class TimeFormat(Enum):
    ISO8601 = 'iso8601'
    UNIX = 'unixtime'

class TimeZone(Enum):
    GMT = 'GMT'
    AUTO = 'AUTO'

class Models(Enum):
    BEST_MATCH='best_match'
    ECMWF_IFS04='ecmwf_ifs04'
    ECMWF_IFS025='ecmwf_ifs025'
    ECMWF_AIFS025='ecmwf_aifs025'
    CMA_GRAPES_GLOBAL='cma_grapes_global'
    BOM_ACCESS_GLOBAL='bom_access_global'
    GFS_SEAMLESS='gfs_seamless'
    GFS_GLOBAL='gfs_global'
    GFS_HRRR='gfs_hrrr'
    NCEP_NBM_CONUS='ncep_nbm_conus'
    GFS_GRAPHCAST025='gfs_graphcast025'
    JMA_SEAMLESS='jma_seamless'
    JMA_MSM='jma_msm'
    JMA_GSM='jma_gsm'
    ICON_SEAMLESS='icon_seamless'
    ICON_GLOBAL='icon_global'
    ICON_EU='icon_eu'
    ICON_D2='icon_d2'
    GEM_SEAMLESS='gem_seamless'
    GEM_GLOBAL='gem_global'
    GEM_REGIONAL='gem_regional'
    GEM_HRDPS_CONTINENTAL='gem_hrdps_continental'
    METEOFRANCE_SEAMLESS='meteofrance_seamless'
    METEOFRANCE_ARPEGE_WORLD='meteofrance_arpege_world'
    METEOFRANCE_ARPEGE_EUROPE='meteofrance_arpege_europe'
    METEOFRANCE_AROME_FRANCE='meteofrance_arome_france'
    METEOFRANCE_AROME_FRANCE_HD='meteofrance_arome_france_hd'
    ARPAE_COSMO_SEAMLESS='arpae_cosmo_seamless'
    ARPAE_COSMO_2I='arpae_cosmo_2i'
    ARPAE_COSMO_5M='arpae_cosmo_5m'
    METNO_SEAMLESS='metno_seamless'
    METNO_NORDIC='metno_nordic'
    KNMI_SEAMLESS='knmi_seamless'
    KNMI_HARMONIE_AROME_EUROPE='knmi_harmonie_arome_europe'
    KNMI_HARMONIE_AROME_NETHERLANDS='knmi_harmonie_arome_netherlands'
    DMI_SEAMLESS='dmi_seamless'
    DMI_HARMONIE_AROME_EUROPE='dmi_harmonie_arome_europe'
    UKMO_SEAMLESS='ukmo_seamless'
    UKMO_GLOBAL_DETERMINISTIC_10KM='ukmo_global_deterministic_10km'
    UKMO_UK_DETERMINISTIC_2KM='ukmo_uk_deterministic_2km'

class CellSelection(Enum):
    LAND = 'land'
    SEA = 'sea'
    NEAREST = 'nearest'

