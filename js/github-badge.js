/*  GitHub Badge, version 1.2.3
 *  (c) 2008 Dr Nic Williams
 *
 *  GitHub Badge is freely distributable under
 *  the terms of an MIT-style license.
 *  For details, see the web site: http://github.com/drnic/github-badges/tree/master
 *
 *--------------------------------------------------------------------------*/
var GITHUB_USERNAME="teepark";var GitHubBadge=GitHubBadge||{Version:"1.2.3"};GitHubBadge.Launcher=new function(){function C(B,A){if("jQuery" in window){jQuery("head").prepend(jQuery('<link rel="stylesheet" type="text/css"></link>').attr("href",B).attr("id",A))}else{alert("nope");document.write('<link rel="stylesheet" href="'+B+'" type="text/css"'+id_attr+"></link>")}}function D(){var B=document.getElementsByTagName("script");for(var A=0;A<B.length;A++){if(B[A].src&&B[A].src.match(/github-badge-launcher\.js(\?.*)?/)){return B[A].src.replace(/github-badge-launcher\.js(\?.*)?/,"")}}}this.init=function(){var G=[[typeof jQuery,"ext/jquery"],[typeof jQuery!="undefined"&&typeof jQuery.template,"ext/jquery.template"],[false,"github-badge"]];var H=document.getElementsByTagName("script");for(var A=0;A<H.length;A++){if(H[A].src&&H[A].src.match(/github-badge-launcher\.js(\?.*)?/)){this.path=H[A].src.replace(/github-badge-launcher\.js(\?.*)?/,"");for(var A=0;A<G.length;A++){if(G[A][0]=="undefined"||!G[A][0]){var B=this.path+G[A][1]+".js";if(A==G.length-1){this.requestContent(B,"GitHubBadge.Launcher.loadedLibraries")}else{this.requestContent(B)}}}break}}};this.loadedLibraries=function(){if(typeof jQuery=="undefined"||typeof jQuery.template=="undefined"){throw ("GitHub Badge requires jQuery and jQuery.template")}var A=("GITHUB_THEME" in window&&GITHUB_THEME)||"white";if(A=="black"||jQuery.color.almostBlack(jQuery("#github-badge").parent().css("background-color"))){C(this.path+"ext/stylesheets/black_badge.css","black_badge")}else{C(this.path+"ext/stylesheets/github-badge.css","badge")}GitHubBadge.buildUserBadge(GITHUB_USERNAME)}};GitHubBadge.Launcher.requestContent=function(C,D){if("jQuery" in window){jQuery.getScript(C,D)}else{onLoadStr=(typeof D=="undefined")?"":'onload="'+D+'()"';document.write("<script "+onLoadStr+'type="text/javascript" src="'+C+'"><\/script>')}};GitHubBadge.Launcher.init();
