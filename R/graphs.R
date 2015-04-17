# Init var
library(RMySQL)
library(ggplot2)
library(pastecs)
library(Hmisc)
library(grid)
library(ggthemes)
library(scales)
library(grid)
library(RColorBrewer)
library(PtProcess)
library(gtable)
library(gridExtra)
# ----------------------------------------------------------------------------
#			THEME
#			Stolen from http://minimaxir.com/2015/02/ggplot-tutorial/
# ----------------------------------------------------------------------------

  # Generate the colors for the chart procedurally with RColorBrewer
  palette <- brewer.pal("Greys", n=9)
  color.background = palette[2]
  color.grid.major = palette[3]
  color.axis.text = palette[6]
  color.axis.title = palette[7]
  color.title = palette[9]
  size.axis.text = 7

fte_theme <- function() {
  # Begin construction of chart
  theme_bw(base_size=9) +

  # Set the entire chart region to a light gray color
  theme(panel.background=element_rect(fill=color.background, color=color.background)) +
  theme(plot.background=element_rect(fill=color.background, color=color.background)) +
  theme(panel.border=element_rect(color=color.background)) +

  # Format the grid
  theme(panel.grid.major=element_line(color=color.grid.major,size=.25)) +
  theme(panel.grid.minor=element_blank()) +
  theme(axis.ticks=element_blank()) +

  # Format the legend, but hide by default
  theme(legend.position="none") +
  theme(legend.background = element_rect(fill=color.background)) +
  theme(legend.text = element_text(size=7,color=color.axis.title)) +

  # Set title and axis labels, and format these and tick marks
  theme(plot.title=element_text(color=color.title, size=10, vjust=1.25)) +
  theme(axis.text.x=element_text(size=size.axis.text,color=color.axis.text)) +
  theme(axis.text.y=element_text(size=size.axis.text,color=color.axis.text)) +
  theme(axis.title.x=element_text(size=8,color=color.axis.title, vjust=0)) +
  theme(axis.title.y=element_text(size=8,color=color.axis.title, vjust=1.25)) +

  # Plot margins
  theme(plot.margin = unit(c(0.35, 0.2, 0.3, 0.35), "cm"))
}

# -------------------------------------------------
#			THEME
# -------------------------------------------------


# working directory
setwd("YOUR_DIRECTORY")

# Load data
dbCon = dbConnect(MySQL(), user="USER", password="PASSWORD", dbname="DB_NAME", unix.socket="SOCKET")
sql = "select distinct 
	i.inspect_camis
	,(1+LOG(if(i.inspect_score_NY>28,28,i.inspect_score_NY))) as score
	,i.inspect_grade as grade
	,venue_rating
	,venue_city
	,venue_cuisine
	,sum(i.inspect_mice) as f_mice
	,sum(i.inspect_flies) as f_flies
	,sum(i.inspect_vermin) as f_vermin
	from inspections i
		left outer join inspections z on z.venue_id = i.venue_id and i.inspect_date < z.inspect_date
		left outer join venues on venues.id = i.venue_id
	where z.inspect_date is null
		and venue_rating > 0
		and i.inspect_grade in ('A','B','C')
		and venue_checkinsCount >= 1000
		and i.inspect_date >= '2013-12-31'
	group by inspect_camis"
rs = dbSendQuery(dbCon, sql)
restaurantData = fetch(rs, n=-1)


# ---------------------------------------------
# Normality graph for hygiene score log
# ---------------------------------------------
#Described var :
title <- "Distribution of hygiene scores"
describedVar <- restaurantData$score
describedVarName <- "Hygiene score (log)"
hist <- ggplot(restaurantData,aes(describedVar)) + geom_histogram(aes(y = ..density..), colour = "black", fill = "white") + labs(x = describedVarName, y = "Density") + stat_function(fun = dnorm, args = list(mean = mean(describedVar, na.rm = TRUE), sd = sd(describedVar, na.rm = TRUE))) + ggtitle(title)

#hist
ggsave(file="hygieneLogDistrib.png", dpi=600, width=4, height=3)

# ---------------------------------------------
# Normality graph for foursquare ratings
# ---------------------------------------------
#Described var :
title <- "Distribution of foursquare ratings"
describedVar <- restaurantData$venue_rating
describedVarName <- "Foursquare rating"
hist <- ggplot(restaurantData,aes(describedVar)) + geom_histogram(aes(y = ..density..), colour = "black", fill = "white") + labs(x = describedVarName, y = "Density") + stat_function(fun = dnorm, args = list(mean = mean(describedVar, na.rm = TRUE), sd = sd(describedVar, na.rm = TRUE))) + ggtitle(title)

	#+ geom_density()
#hist
ggsave(file="foursquareDistrib.png", dpi=600, width=4, height=3)

# ---------------------------------------------
# Scatterplot : foursquare vs hygiene
# ---------------------------------------------
# Variable X
xData = restaurantData$score
xLabel = "Hygiene Score"
yData = restaurantData$venue_rating
yLabel = "Average Foursquare Rating"
title <- "Distribution of foursquare ratings"
# ScatterPlot
scatter <- ggplot(restaurantData,aes(xData, yData)) + geom_point() + geom_smooth() + labs(x = xLabel, y = yLabel)
ggsave(file="foursquareVShygiene.png", dpi=600, width=4, height=3)

# ---------------------------------------------
# Histogram : grade vs average foursquare note
# ---------------------------------------------
title = "Impact of hygiene grade \n on Foursquare notes"
xData = restaurantData$grade
xLabel = "Hygiene Grade"
yData = restaurantData$venue_rating
yLabel = "Average Foursquare Rating"


bar = ggplot(restaurantData,aes(xData, yData, fill=xData)) +
		stat_summary(aes(label=round(..y..,1)), fun.y = mean, geom = "bar") +
		stat_summary(aes(label=round(..y..,1)), fun.y = mean, geom = "text", vjust = -0.25, size=2.5,color=color.axis.text) +
		theme(legend.position="none") +
		fte_theme() +
		labs(x = xLabel, y = yLabel,title=title)
ggsave(file="foursquareVSgrade.png", dpi=600, width=4, height=3)

# ---------------------------------------------
# Histogram : mice vs average foursquare note
# ---------------------------------------------
xData <-factor(restaurantData$f_mice, levels = c(0:1), labels = c("No mice", "Mice"))
xLabel = "Mice factor"
yData = restaurantData$venue_rating
yLabel = "Average Foursquare Rating"
# Foursquare vs DOHMH grades
bar1 = ggplot(restaurantData,aes(xData, yData, fill=xData)) + 
		stat_summary(fun.y = mean, geom = "bar") + 
		labs(x = xLabel, y = yLabel) + 
		#stat_summary(fun.data = mean_cl_normal, geom = "pointrange") +
		stat_summary(aes(label=round(..y..,1)), fun.y=mean, geom="text", vjust = -0.25, size=2.5,color=color.axis.text) +
		fte_theme() +
		theme(legend.position="none")
ggsave(file="miceFactor.png", dpi=600, width=3, height=3)

# ---------------------------------------------
# Histogram : flies vs average foursquare note
# ---------------------------------------------
xData <-factor(restaurantData$f_flies, levels = c(0:1), labels = c("No Flies", "Flies"))
xLabel = "Flies factor"
yData = restaurantData$venue_rating
yLabel = "Average Foursquare Rating"
# Foursquare vs DOHMH grades
bar2 = ggplot(restaurantData,aes(xData, yData, fill=xData)) + 
		stat_summary(fun.y = mean, geom = "bar") + 
		labs(x = xLabel, y = yLabel) + 
		#stat_summary(fun.data = mean_cl_normal, geom = "pointrange") +
		stat_summary(aes(label=round(..y..,1)), fun.y=mean, geom="text", vjust = -0.25, size=2.5,color=color.axis.text) +
		fte_theme() +
		theme(legend.position="none",axis.ticks = element_blank(), axis.text.y = element_blank(),axis.title.y = element_blank())
ggsave(file="fliesFactor.png", dpi=600, width=3, height=3)

# ---------------------------------------------
# Histogram : vermin vs average foursquare note
# ---------------------------------------------
xData <-factor(restaurantData$f_vermin, levels = c(0:1), labels = c("No Vermin", "Vermin"))
xLabel = "Vermin factor"
yData = restaurantData$venue_rating
yLabel = "Average Foursquare Rating"
# Foursquare vs DOHMH grades
bar3 = ggplot(restaurantData,aes(xData, yData, fill=xData)) + 
		stat_summary(fun.y = mean, geom = "bar") + 
		labs(x = xLabel, y = yLabel) + 
		#stat_summary(fun.data = mean_cl_normal, geom = "pointrange") +
		stat_summary(aes(label=round(..y..,1)), fun.y=mean, geom="text", vjust = -0.25, size=2.5,color=color.axis.text) +
		fte_theme() +
		theme(legend.position="none",axis.ticks = element_blank(), axis.text.y = element_blank(),axis.title.y = element_blank())
ggsave(file="verminFactor.png", dpi=600, width=3, height=3)

# ---------------------------------------------
# 3 Histograms : vermin, mice, flies
# ---------------------------------------------
 # New gtable with space for the three plots plus a right-hand margin
gt = gtable(widths = unit(c(1, 1, 1, .3), "null"), height = unit(1, "null"))
gt1 <- ggplot_gtable(ggplot_build(bar1))
gt2 <- ggplot_gtable(ggplot_build(bar2))
gt3 <- ggplot_gtable(ggplot_build(bar3))
# Instert gt1, gt2 and gt2 into the new gtable
gt <- gtable_add_grob(gt, gt1, 1, 1)
gt <- gtable_add_grob(gt, gt2, 1, 2)
gt <- gtable_add_grob(gt, gt3, 1, 3)
title = 'blabla'
grid.newpage()
grid.draw(gt)

