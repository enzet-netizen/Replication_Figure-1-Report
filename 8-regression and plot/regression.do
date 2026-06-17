import delimited "panel.csv", clear

quietly ppmlhdfe monthly_productivity rel_month_p*, absorb(author_id cohort_id##month_id rel_month) vce(cluster author_id)

matrix b = e(b)
matrix V = e(V)
local names : colnames b
tempname memhold
postfile `memhold' str40 coef double estimate double se using ///
    "coefs_stata.csv", replace
local k = 1
foreach name of local names {
    local est = b[1, `k']
    local stderr = sqrt(V[`k', `k'])
    post `memhold' ("`name'") (`est') (`stderr')
    local k = `k' + 1
}
postclose `memhold'
display "Saved: coefs_stata.csv"

coefplot , ///
    keep( ///
        rel_month_pre_12_treated rel_month_pre_11_treated rel_month_pre_10_treated ///
        rel_month_pre_09_treated rel_month_pre_08_treated rel_month_pre_07_treated ///
        rel_month_pre_06_treated rel_month_pre_05_treated rel_month_pre_04_treated ///
        rel_month_pre_03_treated rel_month_pre_02_treated ///
        rel_month_post_01_treated rel_month_post_02_treated rel_month_post_03_treated ///
        rel_month_post_04_treated rel_month_post_05_treated rel_month_post_06_treated ///
        rel_month_post_07_treated rel_month_post_08_treated rel_month_post_09_treated ///
        rel_month_post_10_treated rel_month_post_11_treated rel_month_post_12_treated ///
        rel_month_post_13_treated rel_month_post_14_treated rel_month_post_15_treated ///
        rel_month_post_16_treated rel_month_post_17_treated ///
    ) ///
    vertical yline(0) ///
    coeflabels( ///
        rel_month_pre_12_treated = "-12" rel_month_pre_11_treated = "-11" ///
        rel_month_pre_10_treated = "-10" rel_month_pre_09_treated = "-9" ///
        rel_month_pre_08_treated = "-8" rel_month_pre_07_treated = "-7" ///
        rel_month_pre_06_treated = "-6" rel_month_pre_05_treated = "-5" ///
        rel_month_pre_04_treated = "-4" rel_month_pre_03_treated = "-3" ///
        rel_month_pre_02_treated = "-2" ///
        rel_month_post_01_treated = "1" rel_month_post_02_treated = "2" ///
        rel_month_post_03_treated = "3" rel_month_post_04_treated = "4" ///
        rel_month_post_05_treated = "5" rel_month_post_06_treated = "6" ///
        rel_month_post_07_treated = "7" rel_month_post_08_treated = "8" ///
        rel_month_post_09_treated = "9" rel_month_post_10_treated = "10" ///
        rel_month_post_11_treated = "11" rel_month_post_12_treated = "12" ///
        rel_month_post_13_treated = "13" rel_month_post_14_treated = "14" ///
        rel_month_post_15_treated = "15" rel_month_post_16_treated = "16" ///
        rel_month_post_17_treated = "17" ///
    ) ///
    xtitle("Event time (months)") ytitle("Coefficient") ///
    ylabel(-0.5(0.25)1)

graph export "fig1A_productivity.pdf", replace

matrix b = e(b)
matrix V = e(V)
local names : colnames b
tempname memhold
postfile `memhold' str40 coef double estimate double se using "coefs_stata.dta", replace
local k = 1
foreach name of local names {
    local est = b[1, `k']
    local stderr = sqrt(V[`k', `k'])
    post `memhold' ("`name'") (`est') (`stderr')
    local k = `k' + 1
}
postclose `memhold'
