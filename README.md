# LogoSimilarityChallange


<p><strong>Logo Similarity Challenge</strong></p>
<p><strong>Summary of approach</strong></p>
<p>The challenge can be split in several different tasks that are not related and require specific approaches:</p>
<ol>
<li>Crawling: extracting the html code of the webpages hosted at the respective links</li>
<li>Logo identification: parsing the HTML files to identify images representing logos</li>
<li>Logo extraction</li>
<li>Image classification: classifying the logos with non-AI/ML algorithm approaches</li>
</ol>
<p>My approach was based on the idea that the task is split into basic steps that can be performed independently. Each step was developed separately and, once a basic version of the script for each step was ready, I spent the remaining time optimizing, mostly dealing with corner cases.</p>
<p>During the optimisation stage, I have decided to merge the crawling and logo extraction stages. The reason for this is that at the crawling stage, the HTML is already loaded in memory - while a trivial optimisation it could add up significantly at scale.</p>
<p><strong>Preparation</strong></p>
<p>The list contained 968 double entries; after removing them, the list has 3,416 links, down from 4,384. A unique id was created based on the domain name and the link was also generated beforehand. A semantical grouping of domains was performed at this stage (to be used at the logo matching stage). For the ease of the setup for the purposes of this exercise, the &ldquo;database&rdquo; was a csv file, loaded in a pandas dataframe.</p>
<p><strong><strong>Crawling</strong></strong></p>
<p>The crawling is performed via two scripts:</p>
<ul>
<li>A basic crawler that uses native python requests</li>
<li>An advanced crawler, that makes the requests using crawl4ai</li>
</ul>
<p>Both crawlers start by making a request for the homepage of the website and, if successful, then try to identify the logo by looking for an image that has &ldquo;logo&rdquo; in its name. If such an image is found they try to download it. Both crawlers use threading.</p>
<p>This dual approach was taken because the basic crawler is very fast and has a decent success rate (over 50%). The advanced crawler is able to extract more pages, but it is considerably slower.</p>
<p>Room for improvement:</p>
<ul>
<li>Experimenting with other crawling libraries to circumvent bot detection</li>
<li>Better support for redirects</li>
<li>Proxy/IP rotation to avoid geoblocking</li>
<li>Bypass for cookie consent dialog</li>
</ul>
<p><strong><strong>Logo identification</strong></strong></p>
<p>Several approaches were considered to identify the images containing logos in the html files. The first approach was to identify the first image in the file that contains &ldquo;logo&rdquo; in its file name. This is based on the assumption that the image with the logo would contain the word logo and that the logo is usually displayed in the top-left corner, which would in a majority of cases make it the first image in the file. For this, a regular expression approach was used, as it was considered less computationally intensive.</p>
<p>Room for improvement:</p>
<ul>
<li>Improved logic for identifying the logo: images/elements with link to homepage, parsing of CSS files for background images</li>
</ul>
<p><strong><strong>Logo extraction</strong></strong></p>
<p>Once a logo candidate was identified, its URL was determined and downloaded using a simple http request.</p>
<p>Room for improvement</p>
<ul>
<li>Support for SVG loaded as data</li>
<li>Better identification of invalid files</li>
</ul>
<p><strong><strong>Logo classification</strong></strong></p>
<p>When first reading the task, I thought of various ways to classify images that do not use AI/ML, such as based on color scheme and features, approaches that can be implemented with classic image processing algorithms. However, after seeing the list and the scraped logos, I reasoned that the point of the exercise is to group sites that belong to the same company and therefore have the same (or very similar logo).</p>
<p>Sites that belong to the same company/group are likely to be developed based on templates and are likely to use the same set of graphic resources. The first approach was to simply compare the files based on their checksum, since this is very fast computationally and based on the assumption that websites based on the same template are likely to use a copy of the same logo image.</p>
<p>However, this approach based on checksums fails for files that contain the same image at different sizes, so an image similarity comparison algorithm such as SSIM (Structural Similarity Index Measure) has to be used. This requires a one-to-one comparison of all images, but it can be optimised.</p>
<p>By grouping the domains based on semantic similarity of names, we can hope to identify images that are highly likely to be similar. So, first I compared images from those domain groups that had images in more than one image group. Then a complete one-to-one comparison of remaining image groups was performed.</p>
<p>For the SSIM comparison the images were &ldquo;normalised&rdquo;: converted to RGB and resized to 256x256 pixels. During comparison they were also converted to grayscale.</p>
<p>Results of logo classification:</p>
<table>
<tbody>
<tr>
<td>
<p>Number of images processed</p>
</td>
<td>
<p>2341</p>
</td>
</tr>
<tr>
<td>
<p>Groups based on checksum</p>
</td>
<td>
<p>1260</p>
</td>
</tr>
<tr>
<td>
<p>Groups after 1st grouping (domain similarity)</p>
</td>
<td>
<p>1103</p>
</td>
</tr>
<tr>
<td>
<p>Final number of groups</p>
</td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<p>Room for improvement:</p>
<ul>
<li>Improved image processing for transparency/negative images</li>
<li>Improved resizing for images with different proportions</li>
<li>Improved cropping</li>
<li>More efficient matching algorithms ( if any)</li>
<li>Decrease false positives</li>
</ul>
<p><strong>Scripts (order of processing)</strong></p>
<ol>
<li><strong>crawler.py:</strong> the basic crawler</li>
<li><strong>crawler_advanced.py:</strong> the advanced crawler</li>
<li><strong>checksum_calculator.py:</strong> grouping of logos based on checksum</li>
<li><strong>image_processing_ssim.py:</strong> preparation of images for SSIM comparison</li>
<li><strong>image_regrouping_ssim_domain.py:</strong> first regrouping of images, based on domain name similarity</li>
<li><strong>image_regrouping_ssim_general.py:</strong> final regrouping of images, based on all-with-all comparison</li>
</ol>
<p><br /><br /><br /></p>
